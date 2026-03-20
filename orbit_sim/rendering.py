from __future__ import annotations

import pygame
from pygame import Vector2

from orbit_sim.config import SPACE_HAZE, STAR_CORE, STAR_GLOW, WINDOW_SIZE
from orbit_sim.models import CelestialBody


class SceneRenderer:
    def draw(
        self,
        surface: pygame.Surface,
        scene_center: Vector2,
        bodies: list[CelestialBody],
        zoom: float,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
    ) -> None:
        self.draw_space_haze(surface, zoom)
        self.draw_orbits(surface, scene_center, bodies, zoom, selected_body)
        self.draw_star(surface, zoom)
        self.draw_planets(surface, scene_center, bodies, zoom, hovered_body, selected_body)

    def draw_space_haze(self, surface: pygame.Surface, zoom: float) -> None:
        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        haze_scale = 0.9 + (zoom - 1.0) * 0.18

        for radius, alpha in ((360, 16), (250, 28), (170, 42)):
            pygame.draw.circle(haze, (*SPACE_HAZE, alpha), center, int(radius * haze_scale))

        surface.blit(haze, (0, 0))

    def draw_star(self, surface: pygame.Surface, zoom: float) -> None:
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        star_scale = 0.88 + (zoom - 1.0) * 0.25
        glow_size = int(420 * star_scale)
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_center = (glow_size // 2, glow_size // 2)

        for radius, alpha in ((150, 12), (100, 20), (72, 34), (46, 56)):
            pygame.draw.circle(glow, (*STAR_GLOW, alpha), glow_center, int(radius * star_scale))

        surface.blit(
            glow,
            (center[0] - glow_size // 2, center[1] - glow_size // 2),
            special_flags=pygame.BLEND_ALPHA_SDL2,
        )
        pygame.draw.circle(surface, STAR_GLOW, center, int(22 * star_scale))
        pygame.draw.circle(surface, STAR_CORE, center, int(14 * star_scale))

    def draw_orbits(
        self,
        surface: pygame.Surface,
        scene_center: Vector2,
        bodies: list[CelestialBody],
        zoom: float,
        selected_body: CelestialBody | None,
    ) -> None:
        orbit_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        center = (int(scene_center.x), int(scene_center.y))

        for body in bodies:
            scaled_radius = int(body.orbit_radius * zoom)
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
        scene_center: Vector2,
        bodies: list[CelestialBody],
        zoom: float,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
    ) -> None:
        for body in bodies:
            position = scene_center + body.position() * zoom
            screen_pos = (int(position.x), int(position.y))
            planet_radius = max(4, int(body.radius * zoom))
            glow_size = max(54, planet_radius * 6)
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_center = glow_size // 2
            is_hovered = body is hovered_body
            is_selected = body is selected_body

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
                pygame.draw.circle(surface, ring_color, screen_pos, planet_radius + 7, 1)

            pygame.draw.circle(surface, body.color, screen_pos, planet_radius)
            pygame.draw.circle(
                surface,
                body.accent_color,
                (screen_pos[0] - 3, screen_pos[1] - 3),
                max(2, planet_radius // 3),
            )

