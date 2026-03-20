from __future__ import annotations

from math import asin, pi, sqrt

import pygame
from pygame import Vector2

from orbit_sim.models import CelestialBody
from orbit_sim.planet_textures import PlanetTextureLibrary


class SpinningPlanetRenderer:
    def __init__(self, texture_library: PlanetTextureLibrary | None = None) -> None:
        self.texture_library = texture_library or PlanetTextureLibrary()
        self._tiled_texture_cache: dict[tuple[str, int], pygame.Surface | None] = {}
        self._frame_cache: dict[tuple[str, int, int], pygame.Surface] = {}

    def render(self, body: CelestialBody, diameter: int, simulation_days: float) -> pygame.Surface | None:
        if not self.texture_library.has_texture(body.name):
            return None

        safe_diameter = max(120, int(diameter))
        internal_diameter = max(136, min(280, int(safe_diameter * 0.6)))
        rotation_degrees = self._rotation_degrees(body, simulation_days)
        rotation_index = int((rotation_degrees % 360.0) / 4.0)
        cache_key = (body.name, internal_diameter, rotation_index)
        if cache_key not in self._frame_cache:
            self._frame_cache[cache_key] = self._build_frame(body, internal_diameter, rotation_index * 4.0)

        frame = self._frame_cache[cache_key]
        if frame.get_width() == safe_diameter:
            return frame

        return pygame.transform.smoothscale(frame, (safe_diameter, safe_diameter))

    def clear_frame_cache(self) -> None:
        self._frame_cache.clear()

    def _build_frame(self, body: CelestialBody, diameter: int, rotation_degrees: float) -> pygame.Surface:
        texture = self.texture_library.square_texture(body.name, 720)
        if texture is None:
            return pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        tiled_texture = self._tiled_texture(body.name, texture)
        if tiled_texture is None:
            return pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        sphere = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        radius = diameter / 2
        visible_strip_width = texture.get_width() // 2
        start_x = int(((rotation_degrees / 360.0) % 1.0) * texture.get_width())

        for y in range(diameter):
            y_ratio = ((y + 0.5) / diameter) * 2.0 - 1.0
            if abs(y_ratio) >= 1.0:
                continue

            half_width = sqrt(1.0 - (y_ratio * y_ratio)) * radius
            destination_width = max(1, int(half_width * 2))
            x_position = int(radius - half_width)
            latitude = 0.5 - asin(y_ratio) / pi
            source_y = max(0, min(texture.get_height() - 1, int(latitude * (texture.get_height() - 1))))
            source_row = tiled_texture.subsurface((start_x, source_y, visible_strip_width, 1))
            scaled_row = pygame.transform.smoothscale(source_row, (destination_width, 1))
            sphere.blit(scaled_row, (x_position, y))

        self._apply_lighting(sphere, body)
        return sphere

    def _apply_lighting(self, sphere: pygame.Surface, body: CelestialBody) -> None:
        diameter = sphere.get_width()
        radius = diameter // 2
        center = Vector2(radius, radius)
        light_vector = Vector2(-0.75, -0.28).normalize()
        shadow_vector = -light_vector

        highlight = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(
            highlight,
            (255, 255, 255, 54),
            self._point(center + light_vector * radius * 0.34),
            int(radius * 0.72),
        )
        pygame.draw.circle(
            highlight,
            (*body.accent_color, 42),
            self._point(center + light_vector * radius * 0.5),
            int(radius * 0.44),
        )
        sphere.blit(highlight, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

        shadow = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(
            shadow,
            (0, 0, 0, 112),
            self._point(center + shadow_vector * radius * 0.16),
            int(radius * 1.02),
        )
        pygame.draw.circle(
            shadow,
            (0, 0, 0, 78),
            self._point(center + shadow_vector * radius * 0.38),
            int(radius * 0.76),
        )
        sphere.blit(shadow, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

        rim = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(rim, (*body.accent_color, 58), (radius, radius), radius - 1, max(1, diameter // 90))
        sphere.blit(rim, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _tiled_texture(self, body_name: str, texture: pygame.Surface) -> pygame.Surface | None:
        cache_key = (body_name, texture.get_width())
        if cache_key not in self._tiled_texture_cache:
            tiled = pygame.Surface((texture.get_width() * 2, texture.get_height()))
            tiled.blit(texture, (0, 0))
            tiled.blit(texture, (texture.get_width(), 0))
            self._tiled_texture_cache[cache_key] = tiled.convert()
        return self._tiled_texture_cache[cache_key]

    def _rotation_degrees(self, body: CelestialBody, simulation_days: float) -> float:
        if abs(body.rotation_hours) < 0.01:
            return 0.0

        turns = (simulation_days * 24.0) / body.rotation_hours
        return (turns % 1.0) * 360.0

    def _point(self, vector: Vector2) -> tuple[int, int]:
        return int(vector.x), int(vector.y)
