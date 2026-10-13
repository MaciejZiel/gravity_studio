from __future__ import annotations

from math import asin, atan2, cos, pi, radians, sin, sqrt

import pygame
from pygame import Vector3

from orbit_sim.models import CelestialBody
from orbit_sim.planet_textures import PlanetTextureLibrary


class SpinningPlanetRenderer:
    def __init__(self, texture_library: PlanetTextureLibrary | None = None) -> None:
        self.texture_library = texture_library or PlanetTextureLibrary()
        self._frame_cache: dict[tuple[str, int, int], pygame.Surface] = {}
        self._display_cache: dict[tuple[str, int, int], pygame.Surface] = {}
        self._geometry_cache: dict[tuple[str, int, int], tuple[tuple[int, int, float, float, float, float, float, int], ...]] = {}

    def render(
        self,
        body: CelestialBody,
        diameter: int,
        simulation_days: float,
        display_rotation_degrees: float | None = None,
    ) -> pygame.Surface | None:
        if not self.texture_library.has_texture(body.name):
            return None

        safe_diameter = max(140, int(diameter))
        internal_diameter = max(148, min(288, int(safe_diameter * 0.68)))
        rotation_degrees = self._rotation_degrees(body, simulation_days) if display_rotation_degrees is None else display_rotation_degrees
        rotation_step = 4.0 if safe_diameter >= 220 else 3.0
        rotation_index = int((rotation_degrees % 360.0) / rotation_step)
        cache_key = (body.name, internal_diameter, rotation_index)
        if cache_key not in self._frame_cache:
            self._frame_cache[cache_key] = self._build_frame(body, internal_diameter, rotation_index * rotation_step, simulation_days)

        frame = self._frame_cache[cache_key]
        if frame.get_width() == safe_diameter:
            return frame

        display_key = (body.name, safe_diameter, rotation_index)
        if display_key not in self._display_cache:
            self._display_cache[display_key] = pygame.transform.smoothscale(frame, (safe_diameter, safe_diameter))
            if len(self._display_cache) > 192:
                self._display_cache.clear()
                self._display_cache[display_key] = pygame.transform.smoothscale(frame, (safe_diameter, safe_diameter))
        return self._display_cache[display_key]

    def clear_frame_cache(self) -> None:
        self._frame_cache.clear()
        self._display_cache.clear()
        self._geometry_cache.clear()

    def _build_frame(self, body: CelestialBody, diameter: int, rotation_degrees: float, simulation_days: float) -> pygame.Surface:
        texture = self.texture_library.map_texture(body.name, 1024)
        if texture is None:
            return pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        luminance_rows = self.texture_library.map_luminance(body.name, 1024)
        earth_clouds = self.texture_library.auxiliary_texture("earth_clouds", (texture.get_width(), texture.get_height()))
        earth_night = self.texture_library.auxiliary_texture("earth_night", (texture.get_width(), texture.get_height()))

        sphere = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        texture_width = texture.get_width()
        texture_height = texture.get_height()
        texture_width_limit = texture_width - 1
        rotation_radians = rotation_degrees * pi / 180.0
        light_direction = self._light_direction(body, simulation_days)
        light_x, light_y, light_z = light_direction.x, light_direction.y, light_direction.z
        bump_strength = self._bump_strength(body)
        geometry_samples = self._geometry_samples(body, diameter, texture_height)
        inv_tau = 1.0 / (2 * pi)
        inv_255 = 1.0 / 255.0
        body_name = body.name
        is_earth = body_name == "Earth"
        is_venus = body_name == "Venus"
        is_rocky = body_name in {"Mercury", "Mars"}
        has_terminator_glow = body_name in {"Venus", "Earth", "Mars", "Uranus", "Neptune", "Saturn"}
        terminator_color = self._terminator_color(body)
        has_aurora = body_name in {"Earth", "Jupiter", "Saturn"}
        aurora_color = self._aurora_color(body)
        cloud_rotation = rotation_radians * 1.08 + simulation_days * 0.05 if is_earth and earth_clouds is not None else 0.0
        aurora_floor = radians(48.0)
        aurora_span = radians(26.0)
        texture.lock()
        sphere.lock()

        for x, y, normal_x, normal_y, normal_z, base_longitude, latitude, source_y in geometry_samples:
            longitude = base_longitude + rotation_radians
            source_x = min(texture_width_limit, int((((longitude * inv_tau) + 0.5) % 1.0) * texture_width_limit))
            source_color = texture.get_at((source_x, source_y))

            if bump_strength > 0.0 and luminance_rows is not None:
                row = luminance_rows[source_y]
                left = row[max(0, source_x - 1)] * inv_255
                right = row[min(texture_width_limit, source_x + 1)] * inv_255
                up = luminance_rows[max(0, source_y - 1)][source_x] * inv_255
                down = luminance_rows[min(texture_height - 1, source_y + 1)][source_x] * inv_255
                shaded_x = normal_x + (left - right) * bump_strength
                shaded_y = normal_y + (down - up) * bump_strength
                shaded_z = normal_z
                inverse_length = 1.0 / sqrt(shaded_x * shaded_x + shaded_y * shaded_y + shaded_z * shaded_z)
                diffuse = max(0.0, (shaded_x * light_x + shaded_y * light_y + shaded_z * light_z) * inverse_length)
            else:
                diffuse = max(0.0, normal_x * light_x + normal_y * light_y + normal_z * light_z)

            intensity = min(1.12, 0.22 + diffuse * 0.9)
            if is_earth:
                ocean_bias = max(0.0, min(1.0, (source_color.b - source_color.r * 0.7) / 140.0))
                specular_strength = 0.18 + ocean_bias * 1.1
            elif is_venus:
                specular_strength = 0.12
            elif is_rocky:
                specular_strength = 0.08
            else:
                specular_strength = 0.04
            specular = max(0.0, diffuse - 0.9) * specular_strength

            color_r = min(255, int(source_color.r * intensity + 255 * specular))
            color_g = min(255, int(source_color.g * intensity + 248 * specular))
            color_b = min(255, int(source_color.b * intensity + 236 * specular))

            if has_terminator_glow:
                glow_amount = max(0.0, 0.22 - abs(diffuse - 0.12)) / 0.22
                if glow_amount > 0.0:
                    blend_amount = min(0.24, glow_amount * 0.22)
                    color_r = int(color_r * (1.0 - blend_amount) + terminator_color[0] * blend_amount)
                    color_g = int(color_g * (1.0 - blend_amount) + terminator_color[1] * blend_amount)
                    color_b = int(color_b * (1.0 - blend_amount) + terminator_color[2] * blend_amount)

            if is_earth and earth_night is not None:
                night_mix = max(0.0, (0.34 - diffuse) / 0.34)
                if night_mix > 0.0:
                    night_color = earth_night.get_at((source_x, source_y))
                    emission_amount = night_mix * 0.8
                    color_r = min(255, int(color_r + night_color.r * emission_amount))
                    color_g = min(255, int(color_g + night_color.g * emission_amount))
                    color_b = min(255, int(color_b + night_color.b * emission_amount))

            if is_earth and earth_clouds is not None:
                cloud_x = min(texture_width_limit, int((((base_longitude + cloud_rotation) * inv_tau + 0.5) % 1.0) * texture_width_limit))
                cloud_color = earth_clouds.get_at((cloud_x, source_y))
                cloud_mix = max(0.0, (self._luminance(cloud_color) - 0.46) * 1.8)
                if cloud_mix > 0.0:
                    blend_amount = min(0.32, cloud_mix)
                    color_r = int(color_r * (1.0 - blend_amount) + 248 * blend_amount)
                    color_g = int(color_g * (1.0 - blend_amount) + 250 * blend_amount)
                    color_b = int(color_b * (1.0 - blend_amount) + 252 * blend_amount)

            if has_aurora:
                polar_distance = max(0.0, (abs(latitude) - aurora_floor) / aurora_span)
                if polar_distance > 0.0:
                    twilight = max(0.0, min(1.0, (0.38 - diffuse) / 0.38))
                    aurora_mix = min(0.24, polar_distance * twilight * (0.28 if is_earth else 0.18))
                    if aurora_mix > 0.0:
                        color_r = int(color_r * (1.0 - aurora_mix) + aurora_color[0] * aurora_mix)
                        color_g = int(color_g * (1.0 - aurora_mix) + aurora_color[1] * aurora_mix)
                        color_b = int(color_b * (1.0 - aurora_mix) + aurora_color[2] * aurora_mix)

            sphere.set_at((x, y), (color_r, color_g, color_b, 255))

        sphere.unlock()
        texture.unlock()
        self._draw_rim_light(sphere, body)
        self._draw_atmosphere(sphere, body)
        return sphere

    def _geometry_samples(
        self,
        body: CelestialBody,
        diameter: int,
        texture_height: int,
    ) -> tuple[tuple[int, int, float, float, float, float, float, int], ...]:
        cache_key = (body.name, diameter, texture_height)
        if cache_key not in self._geometry_cache:
            radius = diameter / 2
            center = radius - 0.5
            display_tilt = radians(self._display_axial_tilt(body))
            cos_tilt = cos(-display_tilt)
            sin_tilt = sin(-display_tilt)
            samples: list[tuple[int, int, float, float, float, float, float, int]] = []

            for y in range(diameter):
                y_normalized = (y - center) / radius
                for x in range(diameter):
                    x_normalized = (x - center) / radius
                    radial_distance = x_normalized * x_normalized + y_normalized * y_normalized
                    if radial_distance > 1.0:
                        continue

                    z_normalized = sqrt(1.0 - radial_distance)
                    normal_x = x_normalized * cos_tilt - (-y_normalized) * sin_tilt
                    normal_y = x_normalized * sin_tilt + (-y_normalized) * cos_tilt
                    normal_z = z_normalized
                    base_longitude = atan2(normal_x, normal_z)
                    latitude = asin(normal_y)
                    v = max(0.0, min(1.0, 0.5 - latitude / pi))
                    source_y = min(texture_height - 1, int(v * (texture_height - 1)))
                    samples.append((x, y, normal_x, normal_y, normal_z, base_longitude, latitude, source_y))

            self._geometry_cache[cache_key] = tuple(samples)
            if len(self._geometry_cache) > 16:
                self._geometry_cache.clear()
                self._geometry_cache[cache_key] = tuple(samples)
        return self._geometry_cache[cache_key]

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

    def _apply_terminator_glow(
        self,
        body: CelestialBody,
        base_color: tuple[int, int, int, int],
        diffuse: float,
    ) -> tuple[int, int, int, int]:
        if body.name not in {"Venus", "Earth", "Mars", "Uranus", "Neptune", "Saturn"}:
            return base_color

        glow_amount = max(0.0, 0.22 - abs(diffuse - 0.12)) / 0.22
        if glow_amount <= 0.0:
            return base_color
        return self._blend(base_color, self._terminator_color(body), min(0.24, glow_amount * 0.22))

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

    def _bump_vector(
        self,
        luminance_rows: tuple[bytearray, ...] | None,
        texture_width: int,
        texture_height: int,
        x: int,
        y: int,
        strength: float,
    ) -> Vector3:
        if strength <= 0.0 or luminance_rows is None:
            return Vector3()

        left = luminance_rows[y][max(0, x - 1)] / 255.0
        right = luminance_rows[y][min(texture_width - 1, x + 1)] / 255.0
        up = luminance_rows[max(0, y - 1)][x] / 255.0
        down = luminance_rows[min(texture_height - 1, y + 1)][x] / 255.0
        return Vector3((left - right) * strength, (down - up) * strength, 0.0)

    def _aurora_mix(self, body: CelestialBody, latitude: float, diffuse: float) -> float:
        if body.name not in {"Earth", "Jupiter", "Saturn"}:
            return 0.0
        polar_distance = max(0.0, (abs(latitude) - radians(48.0)) / radians(26.0))
        if polar_distance <= 0.0:
            return 0.0
        twilight = max(0.0, min(1.0, (0.38 - diffuse) / 0.38))
        return min(0.24, polar_distance * twilight * (0.28 if body.name == "Earth" else 0.18))

    def _aurora_color(self, body: CelestialBody) -> tuple[int, int, int]:
        if body.name == "Earth":
            return 108, 220, 182
        return 134, 202, 244

    def _terminator_color(self, body: CelestialBody) -> tuple[int, int, int]:
        colors = {
            "Venus": (236, 214, 178),
            "Earth": (126, 178, 236),
            "Mars": (214, 156, 122),
            "Uranus": (194, 230, 236),
            "Neptune": (128, 170, 236),
            "Saturn": (226, 206, 170),
        }
        return colors.get(body.name, body.accent_color)

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
