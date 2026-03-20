from __future__ import annotations

from math import asin, atan2, pi, sqrt

import pygame
from pygame import Vector2

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
            self._frame_cache[cache_key] = self._build_frame(body, internal_diameter, rotation_index * 3.0)

        frame = self._frame_cache[cache_key]
        if frame.get_width() == safe_diameter:
            return frame

        return pygame.transform.smoothscale(frame, (safe_diameter, safe_diameter))

    def clear_frame_cache(self) -> None:
        self._frame_cache.clear()

    def _build_frame(self, body: CelestialBody, diameter: int, rotation_degrees: float) -> pygame.Surface:
        texture = self.texture_library.map_texture(body.name, 1024)
        if texture is None:
            return pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        sphere = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        radius = diameter / 2
        center = radius - 0.5
        texture_width = texture.get_width()
        texture_height = texture.get_height()
        rotation_radians = rotation_degrees * pi / 180.0
        light_direction = Vector2(-0.82, -0.24).normalize()
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
                longitude = atan2(x_normalized, z_normalized) + rotation_radians
                latitude = asin(-y_normalized)
                u = ((longitude / (2 * pi)) + 0.5) % 1.0
                v = max(0.0, min(1.0, 0.5 - latitude / pi))
                source_x = min(texture_width - 1, int(u * (texture_width - 1)))
                source_y = min(texture_height - 1, int(v * (texture_height - 1)))
                source_color = texture.get_at((source_x, source_y))
                lit_color = self._lit_color(source_color, x_normalized, y_normalized, z_normalized, light_direction)
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

    def _lit_color(
        self,
        color: pygame.Color,
        x_normalized: float,
        y_normalized: float,
        z_normalized: float,
        light_direction: Vector2,
    ) -> tuple[int, int, int, int]:
        light_x = light_direction.x
        light_y = light_direction.y
        normal_y = -y_normalized
        diffuse = max(0.0, x_normalized * light_x + normal_y * light_y + z_normalized * 0.74)
        intensity = min(1.12, 0.22 + diffuse * 0.9)
        specular = max(0.0, diffuse - 0.92) * 0.7
        return (
            min(255, int(color.r * intensity + 255 * specular)),
            min(255, int(color.g * intensity + 248 * specular)),
            min(255, int(color.b * intensity + 236 * specular)),
            255,
        )

    def _rotation_degrees(self, body: CelestialBody, simulation_days: float) -> float:
        if abs(body.rotation_hours) < 0.01:
            return 0.0

        turns = (simulation_days * 24.0) / body.rotation_hours
        return (turns % 1.0) * 360.0
