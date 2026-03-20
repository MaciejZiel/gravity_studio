from __future__ import annotations

from math import sin

import pygame
from pygame import Vector2

from orbit_sim.camera import SolarCamera
from orbit_sim.config import SPACE_HAZE, STAR_CORE, STAR_GLOW
from orbit_sim.models import CelestialBody


class SceneRenderer:
    def draw(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        elapsed_time: float,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
    ) -> None:
        self.draw_space_haze(surface, camera.zoom)
        self.draw_orbits(surface, camera, bodies, selected_body)
        self.draw_star(surface, camera, elapsed_time)
        self.draw_planets(surface, camera, bodies, elapsed_time, hovered_body, selected_body)

    def draw_space_haze(self, surface: pygame.Surface, zoom: float) -> None:
        size = surface.get_size()
        haze = pygame.Surface(size, pygame.SRCALPHA)
        center = (size[0] // 2, size[1] // 2)
        haze_scale = 0.9 + (zoom - 1.0) * 0.18

        min_dimension = min(size)
        for radius_factor, alpha in ((0.4, 16), (0.27, 28), (0.18, 42)):
            radius = int(min_dimension * radius_factor)
            pygame.draw.circle(haze, (*SPACE_HAZE, alpha), center, int(radius * haze_scale))

        surface.blit(haze, (0, 0))

    def draw_star(self, surface: pygame.Surface, camera: SolarCamera, elapsed_time: float) -> None:
        center_vector = camera.layout.scene_center
        center = (int(center_vector.x), int(center_vector.y))
        pulse = 1.0 + sin(elapsed_time * 0.9) * 0.018
        base_glow = int(camera.sun_radius() * 15)
        star_scale = pulse
        glow_size = int(base_glow * star_scale)
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_center = (glow_size // 2, glow_size // 2)

        for radius_factor, alpha in ((0.36, 12), (0.24, 20), (0.17, 34), (0.11, 56)):
            pygame.draw.circle(glow, (*STAR_GLOW, alpha), glow_center, max(1, int(glow_size * radius_factor)))

        surface.blit(
            glow,
            (center[0] - glow_size // 2, center[1] - glow_size // 2),
            special_flags=pygame.BLEND_ALPHA_SDL2,
        )
        sun_outer = max(16, int(camera.sun_radius() * star_scale))
        sun_inner = max(10, int(sun_outer * 0.62))
        pygame.draw.circle(surface, STAR_GLOW, center, sun_outer)
        pygame.draw.circle(surface, STAR_CORE, center, sun_inner)

    def draw_orbits(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        selected_body: CelestialBody | None,
    ) -> None:
        orbit_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        center = (int(camera.layout.scene_center.x), int(camera.layout.scene_center.y))

        for body in bodies:
            scaled_radius = int(camera.orbit_radius(body))
            base_color = (86, 109, 156, 42)
            halo_color = (150, 170, 212, 12)
            if body is selected_body:
                base_color = (*body.accent_color, 72)
                halo_color = (*body.color, 24)

            pygame.draw.circle(orbit_surface, base_color, center, scaled_radius, 1)
            pygame.draw.circle(orbit_surface, halo_color, center, scaled_radius + 1, 1)

        surface.blit(orbit_surface, (0, 0))

    def draw_planets(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        elapsed_time: float,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
    ) -> None:
        for body in bodies:
            position = camera.body_position(body)
            screen_pos = (int(position.x), int(position.y))
            planet_radius = max(3, int(camera.planet_radius(body)))
            glow_size = max(54, planet_radius * 6)
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_center = glow_size // 2
            is_hovered = body is hovered_body
            is_selected = body is selected_body
            light_vector = (camera.layout.scene_center - position)
            if light_vector.length_squared() > 0:
                light_vector = light_vector.normalize()
            else:
                light_vector = Vector2(-1, -1).normalize()

            for radius, alpha in (
                (int(planet_radius * 2.35), 18),
                (int(planet_radius * 1.75), 30),
                (int(planet_radius * 1.1), 52),
            ):
                pygame.draw.circle(glow, (*body.color, alpha), (glow_center, glow_center), max(4, radius))

            surface.blit(
                glow,
                (screen_pos[0] - glow_center, screen_pos[1] - glow_center),
                special_flags=pygame.BLEND_ALPHA_SDL2,
            )
            if is_hovered or is_selected:
                ring_color = body.accent_color if is_selected else body.color
                ring_radius = planet_radius + 7 + int(1.5 * (1.0 + sin(elapsed_time * 4.0)))
                pygame.draw.circle(surface, ring_color, screen_pos, ring_radius, 1)

            planet_surface = pygame.Surface((planet_radius * 4, planet_radius * 4), pygame.SRCALPHA)
            local_center = Vector2(planet_radius * 2, planet_radius * 2)
            self._draw_planet_sprite(planet_surface, local_center, planet_radius, body, light_vector)
            surface.blit(
                planet_surface,
                (screen_pos[0] - planet_radius * 2, screen_pos[1] - planet_radius * 2),
            )

    def _draw_planet_sprite(
        self,
        surface: pygame.Surface,
        center: Vector2,
        radius: int,
        body: CelestialBody,
        light_vector: Vector2,
    ) -> None:
        base_color = body.color
        shadow_color = self._darken(body.color, 0.48)
        core_shadow = self._darken(body.color, 0.72)
        rim_color = body.accent_color

        pygame.draw.circle(surface, base_color, self._point(center), radius)
        pygame.draw.circle(surface, (*rim_color, 84), self._point(center), radius, 1)

        shadow_offset = center - light_vector * radius * 0.28
        shadow_radius = int(radius * 0.94)
        pygame.draw.circle(surface, (*shadow_color, 180), self._point(shadow_offset), shadow_radius)
        pygame.draw.circle(surface, base_color, self._point(center + light_vector * radius * 0.08), int(radius * 0.9))
        pygame.draw.circle(
            surface,
            (*core_shadow, 110),
            self._point(center - light_vector * radius * 0.34),
            int(radius * 0.62),
        )

        highlight_center = center + light_vector * radius * 0.34
        pygame.draw.circle(surface, (*rim_color, 148), self._point(highlight_center), max(2, int(radius * 0.38)))
        pygame.draw.circle(
            surface,
            (255, 255, 255, 78),
            self._point(center + light_vector * radius * 0.5),
            max(2, radius // 6),
        )

    def _darken(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(channel * factor))) for channel in color)

    def _point(self, vector: Vector2) -> tuple[int, int]:
        return int(vector.x), int(vector.y)
