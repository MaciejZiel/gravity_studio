from __future__ import annotations

import sys

import pygame
from pygame import Vector2

from orbit_sim.background import StarField
from orbit_sim.config import (
    SPACE_COLOR,
    SPACE_HAZE,
    STAR_CORE,
    STAR_GLOW,
    SUBTITLE_TEXT,
    TARGET_FPS,
    TITLE_TEXT,
    WINDOW_SIZE,
)
from orbit_sim.models import CelestialBody
from orbit_sim.simulation import OrbitalSimulation


class GravityStudioApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gravity Studio")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("segoeui", 24)
        self.caption_font = pygame.font.SysFont("segoeui", 14)
        self.scene_center = Vector2(WINDOW_SIZE[0] / 2, WINDOW_SIZE[1] / 2)
        self.star_field = StarField(WINDOW_SIZE)
        self.simulation = OrbitalSimulation()
        self.elapsed_time = 0.0
        self.hovered_body: CelestialBody | None = None
        self.selected_body: CelestialBody | None = None
        self.running = True

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit(0)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.selected_body = self.body_at_screen_position(Vector2(event.pos))

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        self.simulation.update(dt)
        self.hovered_body = self.body_at_screen_position(Vector2(pygame.mouse.get_pos()))

    def render(self) -> None:
        self.screen.fill(SPACE_COLOR)
        self.star_field.draw(self.screen, self.elapsed_time)
        self.draw_space_haze()
        self.draw_orbits()
        self.draw_star()
        self.draw_planets()
        self.draw_heading()
        pygame.display.flip()

    def draw_space_haze(self) -> None:
        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)

        for radius, alpha in ((360, 16), (250, 28), (170, 42)):
            pygame.draw.circle(haze, (*SPACE_HAZE, alpha), center, radius)

        self.screen.blit(haze, (0, 0))

    def draw_star(self) -> None:
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        glow = pygame.Surface((420, 420), pygame.SRCALPHA)
        glow_center = (210, 210)

        for radius, alpha in ((150, 12), (100, 20), (72, 34), (46, 56)):
            pygame.draw.circle(glow, (*STAR_GLOW, alpha), glow_center, radius)

        self.screen.blit(glow, (center[0] - 210, center[1] - 210), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(self.screen, STAR_GLOW, center, 22)
        pygame.draw.circle(self.screen, STAR_CORE, center, 14)

    def draw_orbits(self) -> None:
        orbit_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        center = (int(self.scene_center.x), int(self.scene_center.y))

        for body in self.simulation.bodies:
            radius = int(body.orbit_radius)
            pygame.draw.circle(orbit_surface, (86, 109, 156, 42), center, radius, 1)
            pygame.draw.circle(orbit_surface, (150, 170, 212, 12), center, radius + 1, 1)

        self.screen.blit(orbit_surface, (0, 0))

    def draw_heading(self) -> None:
        title = self.title_font.render("GRAVITY STUDIO", True, TITLE_TEXT)
        subtitle = self.caption_font.render("Orbital motion study", True, SUBTITLE_TEXT)
        self.screen.blit(title, (44, 34))
        self.screen.blit(subtitle, (46, 66))

    def draw_planets(self) -> None:
        for body in self.simulation.bodies:
            position = self.body_screen_position(body)
            screen_pos = (int(position.x), int(position.y))
            glow = pygame.Surface((90, 90), pygame.SRCALPHA)
            is_hovered = body is self.hovered_body
            is_selected = body is self.selected_body

            for radius, alpha in ((24, 20), (18, 32), (12, 52)):
                pygame.draw.circle(glow, (*body.color, alpha), (45, 45), radius)

            self.screen.blit(
                glow,
                (screen_pos[0] - 45, screen_pos[1] - 45),
                special_flags=pygame.BLEND_ALPHA_SDL2,
            )
            if is_hovered or is_selected:
                ring_color = body.accent_color if is_selected else body.color
                pygame.draw.circle(self.screen, ring_color, screen_pos, int(body.radius) + 7, 1)
            pygame.draw.circle(self.screen, body.color, screen_pos, int(body.radius))
            pygame.draw.circle(
                self.screen,
                body.accent_color,
                (screen_pos[0] - 3, screen_pos[1] - 3),
                max(2, int(body.radius // 3)),
            )

    def body_screen_position(self, body: CelestialBody) -> Vector2:
        return self.scene_center + body.position()

    def body_at_screen_position(self, screen_position: Vector2) -> CelestialBody | None:
        for body in reversed(self.simulation.bodies):
            if screen_position.distance_to(self.body_screen_position(body)) <= body.radius + 6:
                return body

        return None
