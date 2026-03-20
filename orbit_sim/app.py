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
from orbit_sim.ui import ControlBar, InfoPanel


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
        self.info_panel = InfoPanel()
        self.control_bar = ControlBar()
        self.elapsed_time = 0.0
        self.hovered_body: CelestialBody | None = None
        self.selected_body: CelestialBody | None = None
        self.panel_body: CelestialBody | None = None
        self.panel_visibility = 0.0
        self.hovered_action: str | None = None
        self.control_buttons = self.control_bar.build_buttons(*WINDOW_SIZE, paused=False)
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.paused = False
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
                action = self.action_at_screen_position(event.pos)
                if action is not None:
                    self.handle_action(action)
                else:
                    self.selected_body = self.body_at_screen_position(Vector2(event.pos))
            elif event.type == pygame.MOUSEWHEEL:
                self.target_zoom = max(0.65, min(1.85, self.target_zoom + event.y * 0.08))

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if not self.paused:
            self.simulation.update(dt)
        self.zoom += (self.target_zoom - self.zoom) * min(1.0, dt * 8.0)
        self.control_buttons = self.control_bar.build_buttons(*WINDOW_SIZE, paused=self.paused)
        self.hovered_action = self.action_at_screen_position(pygame.mouse.get_pos())
        self.hovered_body = self.body_at_screen_position(Vector2(pygame.mouse.get_pos()))
        if self.selected_body is not None:
            self.panel_body = self.selected_body

        target_visibility = 1.0 if self.selected_body else 0.0
        self.panel_visibility += (target_visibility - self.panel_visibility) * min(1.0, dt * 10.0)
        if self.selected_body is None and self.panel_visibility < 0.02:
            self.panel_body = None

    def render(self) -> None:
        self.screen.fill(SPACE_COLOR)
        self.star_field.draw(self.screen, self.elapsed_time)
        self.draw_space_haze()
        self.draw_orbits()
        self.draw_star()
        self.draw_planets()
        self.draw_heading()
        self.draw_info_panel()
        self.draw_controls()
        pygame.display.flip()

    def draw_space_haze(self) -> None:
        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        haze_scale = 0.9 + (self.zoom - 1.0) * 0.18

        for radius, alpha in ((360, 16), (250, 28), (170, 42)):
            pygame.draw.circle(haze, (*SPACE_HAZE, alpha), center, int(radius * haze_scale))

        self.screen.blit(haze, (0, 0))

    def draw_star(self) -> None:
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        star_scale = 0.88 + (self.zoom - 1.0) * 0.25
        glow_size = int(420 * star_scale)
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_center = (glow_size // 2, glow_size // 2)

        for radius, alpha in ((150, 12), (100, 20), (72, 34), (46, 56)):
            pygame.draw.circle(glow, (*STAR_GLOW, alpha), glow_center, int(radius * star_scale))

        self.screen.blit(
            glow,
            (center[0] - glow_size // 2, center[1] - glow_size // 2),
            special_flags=pygame.BLEND_ALPHA_SDL2,
        )
        pygame.draw.circle(self.screen, STAR_GLOW, center, int(22 * star_scale))
        pygame.draw.circle(self.screen, STAR_CORE, center, int(14 * star_scale))

    def draw_orbits(self) -> None:
        orbit_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        center = (int(self.scene_center.x), int(self.scene_center.y))

        for body in self.simulation.bodies:
            radius = int(body.orbit_radius)
            scaled_radius = int(radius * self.zoom)
            pygame.draw.circle(orbit_surface, (86, 109, 156, 42), center, scaled_radius, 1)
            pygame.draw.circle(orbit_surface, (150, 170, 212, 12), center, scaled_radius + 1, 1)

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
            planet_radius = max(4, int(body.radius * self.zoom))
            glow_size = max(54, planet_radius * 6)
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_center = glow_size // 2
            is_hovered = body is self.hovered_body
            is_selected = body is self.selected_body

            for radius, alpha in (
                (int(planet_radius * 2.35), 18),
                (int(planet_radius * 1.75), 30),
                (int(planet_radius * 1.1), 52),
            ):
                pygame.draw.circle(glow, (*body.color, alpha), (glow_center, glow_center), max(4, radius))

            self.screen.blit(
                glow,
                (screen_pos[0] - glow_center, screen_pos[1] - glow_center),
                special_flags=pygame.BLEND_ALPHA_SDL2,
            )
            if is_hovered or is_selected:
                ring_color = body.accent_color if is_selected else body.color
                pygame.draw.circle(self.screen, ring_color, screen_pos, planet_radius + 7, 1)
            pygame.draw.circle(self.screen, body.color, screen_pos, planet_radius)
            pygame.draw.circle(
                self.screen,
                body.accent_color,
                (screen_pos[0] - 3, screen_pos[1] - 3),
                max(2, planet_radius // 3),
            )

    def body_screen_position(self, body: CelestialBody) -> Vector2:
        return self.scene_center + body.position() * self.zoom

    def body_at_screen_position(self, screen_position: Vector2) -> CelestialBody | None:
        for body in reversed(self.simulation.bodies):
            if screen_position.distance_to(self.body_screen_position(body)) <= max(4, body.radius * self.zoom) + 6:
                return body

        return None

    def draw_info_panel(self) -> None:
        if self.panel_body is not None and self.panel_visibility > 0.01:
            self.info_panel.draw(self.screen, self.panel_body, self.panel_visibility)

    def draw_controls(self) -> None:
        self.control_bar.draw(self.screen, self.control_buttons, self.hovered_action)

    def action_at_screen_position(self, position: tuple[int, int]) -> str | None:
        for button in self.control_buttons:
            if button.rect.collidepoint(position):
                return button.action

        return None

    def handle_action(self, action: str) -> None:
        if action == "toggle_pause":
            self.paused = not self.paused
        elif action == "reset":
            self.simulation.reset()
            self.zoom = 1.0
            self.target_zoom = 1.0
            self.paused = False
            self.selected_body = None
            self.panel_body = None
            self.panel_visibility = 0.0
        elif action == "add_planet":
            self.selected_body = self.simulation.add_body()
