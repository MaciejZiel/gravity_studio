from __future__ import annotations

from math import asin, atan2, cos, pi, radians, sin, sqrt

import pygame
from pygame import Vector2, Vector3

from orbit_sim.models import CelestialBody
from orbit_sim.planet_textures import PlanetTextureLibrary


class SpinningPlanetRenderer:
    def __init__(self, texture_library: PlanetTextureLibrary | None = None) -> None:
        self.texture_library = texture_library or PlanetTextureLibrary()
        self._frame_cache: dict[tuple[str, int, int], pygame.Surface] = {}

    def render(
        self,
        body: CelestialBody,
        diameter: int,
        simulation_days: float,
        rotation_offset_degrees: float = 0.0,
    ) -> pygame.Surface | None:
        if not self.texture_library.has_texture(body.name):
            return None

        safe_diameter = max(140, int(diameter))
        internal_diameter = max(160, min(320, int(safe_diameter * 0.74)))
        rotation_degrees = self._rotation_degrees(body, simulation_days) + rotation_offset_degrees
        rotation_index = int((rotation_degrees % 360.0) / 3.0)
        cache_key = (body.name, internal_diameter, rotation_index)
        if cache_key not in self._frame_cache:
            self._frame_cache[cache_key] = self._build_frame(body, internal_diameter, rotation_index * 3.0, simulation_days)

        frame = self._frame_cache[cache_key]
        if frame.get_width() == safe_diameter:
            return frame

        return pygame.transform.smoothscale(frame, (safe_diameter, safe_diameter))

    def clear_frame_cache(self) -> None:
        self._frame_cache.clear()

    def _build_frame(self, body: CelestialBody, diameter: int, rotation_degrees: float, simulation_days: float) -> pygame.Surface:
        texture = self.texture_library.map_texture(body.name, 1024)
        if texture is None:
            return pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        earth_clouds = self.texture_library.auxiliary_texture("earth_clouds", (texture.get_width(), texture.get_height()))
        earth_night = self.texture_library.auxiliary_texture("earth_night", (texture.get_width(), texture.get_height()))

        sphere = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        radius = diameter / 2
        center = radius - 0.5
        texture_width = texture.get_width()
        texture_height = texture.get_height()
        rotation_radians = rotation_degrees * pi / 180.0
        light_direction = self._light_direction(body, simulation_days)
        display_tilt = radians(self._display_axial_tilt(body))
        bump_strength = self._bump_strength(body)
        texture.lock()
        sphere.lock()

        for y in range(diameter):
            y_normalized = (y - center) / radius
            for x in range(diameter):
                x_normalized = (x - center) / radius
                radial_distance = x_normalized * x_normalized + y_normalized * y_normalized
                if radial_distance > 1.0:
                    continue

                z_normalized = sqrt(1.0 - radial_distance)
                surface_normal = self._rotate_z(
                    Vector3(x_normalized, -y_normalized, z_normalized),
                    -display_tilt,
                )
                longitude = atan2(surface_normal.x, surface_normal.z) + rotation_radians
                latitude = asin(surface_normal.y)
                u = ((longitude / (2 * pi)) + 0.5) % 1.0
                v = max(0.0, min(1.0, 0.5 - latitude / pi))
                source_x = min(texture_width - 1, int(u * (texture_width - 1)))
                source_y = min(texture_height - 1, int(v * (texture_height - 1)))
                source_color = texture.get_at((source_x, source_y))
                bump = self._bump_vector(texture, source_x, source_y, bump_strength)
                shaded_normal = (surface_normal + bump).normalize()
                diffuse = max(0.0, shaded_normal.dot(light_direction))
                lit_color = self._shade_color(body, source_color, diffuse)
                if body.name == "Earth" and earth_night is not None:
                    night_color = earth_night.get_at((source_x, source_y))
                    night_mix = max(0.0, (0.34 - diffuse) / 0.34)
                    lit_color = self._add_light_emission(lit_color, night_color, night_mix * 0.8)
                if body.name == "Earth" and earth_clouds is not None:
                    cloud_rotation = rotation_radians * 1.08 + simulation_days * 0.05
                    cloud_u = ((atan2(surface_normal.x, surface_normal.z) + cloud_rotation) / (2 * pi) + 0.5) % 1.0
                    cloud_x = min(texture_width - 1, int(cloud_u * (texture_width - 1)))
                    cloud_color = earth_clouds.get_at((cloud_x, source_y))
                    cloud_mix = max(0.0, (self._luminance(cloud_color) - 0.46) * 1.8)
                    lit_color = self._blend(lit_color, (248, 250, 252), min(0.32, cloud_mix))
                sphere.set_at((x, y), lit_color)

        sphere.unlock()
        texture.unlock()
        self._draw_rim_light(sphere, body)
        self._draw_atmosphere(sphere, body)
        return sphere

    def _draw_rim_light(self, sphere: pygame.Surface, body: CelestialBody) -> None:
        radius = sphere.get_width() // 2
        rim = pygame.Surface(sphere.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(rim, (*body.accent_color, 42), (radius, radius), radius - 1, max(1, sphere.get_width() // 96))
        pygame.draw.circle(rim, (255, 255, 255, 20), (int(radius * 0.72), int(radius * 0.62)), int(radius * 0.28))
        sphere.blit(rim, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_atmosphere(self, sphere: pygame.Surface, body: CelestialBody) -> None:
        atmosphere_colors = {
            "Venus": (232, 212, 176, 26),
            "Earth": (122, 176, 236, 34),
            "Mars": (208, 154, 126, 14),
            "Uranus": (190, 228, 236, 24),
            "Neptune": (130, 172, 232, 26),
        }
        if body.name not in atmosphere_colors:
            return

        radius = sphere.get_width() // 2
        atmosphere = pygame.Surface(sphere.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(atmosphere, atmosphere_colors[body.name], (radius, radius), int(radius * 1.02), max(1, sphere.get_width() // 64))
        sphere.blit(atmosphere, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _shade_color(
        self,
        body: CelestialBody,
        color: pygame.Color,
        diffuse: float,
    ) -> tuple[int, int, int, int]:
        intensity = min(1.12, 0.22 + diffuse * 0.9)
        specular = max(0.0, diffuse - 0.9) * self._specular_strength(body, color)
        return (
            min(255, int(color.r * intensity + 255 * specular)),
            min(255, int(color.g * intensity + 248 * specular)),
            min(255, int(color.b * intensity + 236 * specular)),
            255,
        )

    def _add_light_emission(
        self,
        base_color: tuple[int, int, int, int],
        emission: pygame.Color,
        amount: float,
    ) -> tuple[int, int, int, int]:
        return (
            min(255, int(base_color[0] + emission.r * amount)),
            min(255, int(base_color[1] + emission.g * amount)),
            min(255, int(base_color[2] + emission.b * amount)),
            255,
        )

    def _blend(
        self,
        base_color: tuple[int, int, int, int],
        target_color: tuple[int, int, int],
        amount: float,
    ) -> tuple[int, int, int, int]:
        return (
            int(base_color[0] * (1.0 - amount) + target_color[0] * amount),
            int(base_color[1] * (1.0 - amount) + target_color[1] * amount),
            int(base_color[2] * (1.0 - amount) + target_color[2] * amount),
            255,
        )

    def _light_direction(self, body: CelestialBody, simulation_days: float) -> Vector3:
        seasonal_phase = (body.angle - radians(body.season_offset_deg)) + simulation_days * 0.00012
        subsolar_latitude = sin(seasonal_phase) * sin(radians(body.axial_tilt_deg))
        return Vector3(-0.8, subsolar_latitude * 0.9, 0.72).normalize()

    def _display_axial_tilt(self, body: CelestialBody) -> float:
        tilt = body.axial_tilt_deg
        if tilt > 90.0:
            tilt = 180.0 - tilt
        return max(-82.0, min(82.0, tilt))

    def _bump_strength(self, body: CelestialBody) -> float:
        if body.name in {"Mercury", "Mars"}:
            return 0.22
        if body.name == "Earth":
            return 0.18
        if body.name in {"Jupiter", "Saturn", "Uranus", "Neptune"}:
            return 0.08
        return 0.12

    def _specular_strength(self, body: CelestialBody, color: pygame.Color) -> float:
        if body.name == "Earth":
            ocean_bias = max(0.0, min(1.0, (color.b - color.r * 0.7) / 140.0))
            return 0.18 + ocean_bias * 1.1
        if body.name == "Venus":
            return 0.12
        if body.name in {"Mercury", "Mars"}:
            return 0.08
        return 0.04

    def _bump_vector(self, texture: pygame.Surface, x: int, y: int, strength: float) -> Vector3:
        if strength <= 0.0:
            return Vector3()

        left = self._luminance(texture.get_at((max(0, x - 1), y)))
        right = self._luminance(texture.get_at((min(texture.get_width() - 1, x + 1), y)))
        up = self._luminance(texture.get_at((x, max(0, y - 1))))
        down = self._luminance(texture.get_at((x, min(texture.get_height() - 1, y + 1))))
        return Vector3((left - right) * strength, (down - up) * strength, 0.0)

    def _luminance(self, color: pygame.Color) -> float:
        return (color.r * 0.2126 + color.g * 0.7152 + color.b * 0.0722) / 255.0

    def _rotate_z(self, vector: Vector3, angle_radians: float) -> Vector3:
        return Vector3(
            vector.x * cos(angle_radians) - vector.y * sin(angle_radians),
            vector.x * sin(angle_radians) + vector.y * cos(angle_radians),
            vector.z,
        )

    def _rotation_degrees(self, body: CelestialBody, simulation_days: float) -> float:
        if abs(body.rotation_hours) < 0.01:
            return 0.0

        turns = (simulation_days * 24.0) / body.rotation_hours
        return (turns % 1.0) * 360.0
