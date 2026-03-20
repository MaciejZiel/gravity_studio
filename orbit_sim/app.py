from __future__ import annotations

import sys

import pygame
from pygame import Vector2

from orbit_sim.background import StarField
from orbit_sim.camera import SolarCamera
from orbit_sim.config import (
    FALLBACK_WINDOW_SIZE,
    SPACE_COLOR,
    TARGET_FPS,
)
from orbit_sim.models import CelestialBody
from orbit_sim.rendering import SceneRenderer
from orbit_sim.simulation import OrbitalSimulation
from orbit_sim.ui import ControlBar, HudChrome, InfoPanel


class GravityStudioApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gravity Studio: Solar System")
        self.viewport = self._detect_viewport()
        self.screen = self._create_display_surface()
        self.clock = pygame.time.Clock()
        self.camera = SolarCamera(self.viewport)
        self.star_field = StarField(self.viewport)
        self.simulation = OrbitalSimulation()
        self.hud = HudChrome()
        self.info_panel = InfoPanel()
        self.control_bar = ControlBar()
        self.scene_renderer = SceneRenderer()
        self.elapsed_time = 0.0
        self.hovered_body: CelestialBody | None = None
        self.selected_body: CelestialBody | None = None
        self.panel_body: CelestialBody | None = None
        self.panel_visibility = 0.0
        self.hovered_action: str | None = None
        self.show_orbits = True
        self.show_labels = True
        self.control_buttons = self.control_bar.build_buttons(
            *self.viewport,
            self.camera.layout.ui_scale,
            paused=False,
            show_orbits=self.show_orbits,
            show_labels=self.show_labels,
            scale_mode=self.camera.scale_mode,
        )
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
                    self.camera.set_focus_body(self.selected_body)
            elif event.type == pygame.MOUSEWHEEL:
                self.camera.adjust_zoom(event.y * 0.08)

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if not self.paused:
            self.simulation.update(dt)
        self.camera.update(dt, self.elapsed_time)
        self.control_buttons = self.control_bar.build_buttons(
            *self.viewport,
            self.camera.layout.ui_scale,
            paused=self.paused,
            show_orbits=self.show_orbits,
            show_labels=self.show_labels,
            scale_mode=self.camera.scale_mode,
        )
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
        self.scene_renderer.draw(
            self.screen,
            self.camera,
            self.simulation.bodies,
            self.elapsed_time,
            self.hovered_body,
            self.selected_body,
            self.show_orbits,
            self.show_labels,
        )
        self.draw_hud()
        self.draw_info_panel()
        self.draw_controls()
        pygame.display.flip()

    def body_screen_position(self, body: CelestialBody) -> Vector2:
        return self.camera.body_position(body)

    def body_at_screen_position(self, screen_position: Vector2) -> CelestialBody | None:
        for body in reversed(self.simulation.bodies):
            if screen_position.distance_to(self.body_screen_position(body)) <= self.camera.planet_radius(body) + 6:
                return body

        return None

    def draw_info_panel(self) -> None:
        if self.panel_body is not None and self.panel_visibility > 0.01:
            self.info_panel.draw(self.screen, self.panel_body, self.panel_visibility, self.camera.layout.ui_scale)

    def draw_controls(self) -> None:
        self.control_bar.draw(self.screen, self.control_buttons, self.hovered_action, self.camera.layout.ui_scale)

    def draw_hud(self) -> None:
        self.hud.draw(self.screen, self.paused, self.camera.zoom, self.camera.scale_mode, self.camera.layout.ui_scale)

    def action_at_screen_position(self, position: tuple[int, int]) -> str | None:
        for button in self.control_buttons:
            if button.rect.collidepoint(position):
                return button.action

        return None

    def handle_action(self, action: str) -> None:
        if action == "toggle_pause":
            self.paused = not self.paused
        elif action == "toggle_orbits":
            self.show_orbits = not self.show_orbits
        elif action == "toggle_labels":
            self.show_labels = not self.show_labels
        elif action == "toggle_scale":
            self.camera.toggle_scale_mode()
        elif action == "reset":
            self.simulation.reset()
            self.camera.reset()
            self.paused = False
            self.selected_body = None
            self.panel_body = None
            self.panel_visibility = 0.0

    def _detect_viewport(self) -> tuple[int, int]:
        info = pygame.display.Info()
        width = info.current_w or FALLBACK_WINDOW_SIZE[0]
        height = info.current_h or FALLBACK_WINDOW_SIZE[1]
        return width, height

    def _create_display_surface(self) -> pygame.Surface:
        driver = pygame.display.get_driver()
        if driver == "dummy":
            return pygame.display.set_mode(self.viewport)

        return pygame.display.set_mode(self.viewport, pygame.FULLSCREEN)
