from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

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
from orbit_sim.ui import ControlBar, HudChrome, InfoPanel, SceneStrip, TimelineStrip


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
        self.scene_strip = SceneStrip()
        self.timeline_strip = TimelineStrip()
        self.scene_renderer = SceneRenderer()
        self.elapsed_time = 0.0
        self.hovered_body: CelestialBody | None = None
        self.selected_body: CelestialBody | None = None
        self.panel_body: CelestialBody | None = None
        self.panel_visibility = 0.0
        self.hovered_action: str | None = None
        self.show_orbits = True
        self.show_labels = True
        self.ui_hidden = False
        self.notification_text: str | None = None
        self.notification_timer = 0.0
        self.control_buttons = self.control_bar.build_buttons(
            *self.viewport,
            self.camera.layout.ui_scale,
            paused=False,
            show_orbits=self.show_orbits,
            show_labels=self.show_labels,
            scale_mode=self.camera.scale_mode,
        )
        self.timeline_buttons = self.timeline_strip.build_speed_buttons(
            *self.viewport,
            self.camera.layout.ui_scale,
            self.simulation.time_speed_index,
        )
        self.timeline_slider = self.timeline_strip.build_slider(
            *self.viewport,
            self.camera.layout.ui_scale,
            self.simulation.simulation_days / self.simulation.timeline_range_days,
        )
        self.scene_buttons = self.scene_strip.build_buttons(
            self.viewport[0],
            self.camera.layout.ui_scale,
            self.camera.scene_mode,
            self.selected_body is not None,
        )
        self.dragging_timeline = False
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
                action = None if self.ui_hidden else self.action_at_screen_position(event.pos)
                if action is not None:
                    self.handle_action(action)
                elif not self.ui_hidden and self.timeline_hit_test(event.pos):
                    self.dragging_timeline = True
                    self.update_timeline_from_pointer(event.pos[0])
                else:
                    self.selected_body = self.body_at_screen_position(Vector2(event.pos))
                    self.camera.set_focus_body(self.selected_body)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_timeline = False
            elif event.type == pygame.MOUSEMOTION and self.dragging_timeline:
                self.update_timeline_from_pointer(event.pos[0])
            elif event.type == pygame.MOUSEWHEEL:
                self.camera.adjust_zoom(event.y * 0.08)
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if not self.paused and not self.dragging_timeline:
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
        self.timeline_buttons = self.timeline_strip.build_speed_buttons(
            *self.viewport,
            self.camera.layout.ui_scale,
            self.simulation.time_speed_index,
        )
        self.timeline_slider = self.timeline_strip.build_slider(
            *self.viewport,
            self.camera.layout.ui_scale,
            self.simulation.simulation_days / self.simulation.timeline_range_days,
        )
        self.scene_buttons = self.scene_strip.build_buttons(
            self.viewport[0],
            self.camera.layout.ui_scale,
            self.camera.scene_mode,
            self.selected_body is not None,
        )
        self.hovered_action = self.action_at_screen_position(pygame.mouse.get_pos())
        self.hovered_body = self.body_at_screen_position(Vector2(pygame.mouse.get_pos()))
        if self.selected_body is not None:
            self.panel_body = self.selected_body

        target_visibility = 1.0 if self.selected_body else 0.0
        self.panel_visibility += (target_visibility - self.panel_visibility) * min(1.0, dt * 10.0)
        if self.selected_body is None and self.panel_visibility < 0.02:
            self.panel_body = None
        if self.notification_timer > 0.0:
            self.notification_timer = max(0.0, self.notification_timer - dt)
            if self.notification_timer == 0.0:
                self.notification_text = None

    def render(self) -> None:
        self.screen.fill(SPACE_COLOR)
        self.star_field.draw(self.screen, self.elapsed_time)
        self.scene_renderer.draw(
            self.screen,
            self.camera,
            self.simulation.bodies,
            self.elapsed_time,
            self.simulation.simulation_days,
            self.hovered_body,
            self.selected_body,
            self.show_orbits,
            self.show_labels,
        )
        if not self.ui_hidden:
            self.draw_hud()
            self.draw_info_panel()
            self.draw_controls()
            self.draw_timeline()
            self.draw_scene_buttons()
        self.draw_intro_fade()
        self.draw_notification()
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
        local_now = datetime.now().astimezone()
        self.hud.draw(
            self.screen,
            self.paused,
            self.camera.zoom,
            self.camera.scale_mode,
            self.camera.scene_label,
            self.simulation.time_speed_label,
            local_now.strftime("%H:%M:%S"),
            local_now.strftime("%Z"),
            self.camera.layout.ui_scale,
        )

    def draw_timeline(self) -> None:
        date_label = self.simulation.current_datetime().strftime("%b %d, %Y  %H:%M:%S")
        self.timeline_strip.draw(
            self.screen,
            self.timeline_buttons,
            self.timeline_slider,
            date_label,
            self.camera.layout.ui_scale,
        )

    def draw_scene_buttons(self) -> None:
        self.scene_strip.draw(self.screen, self.scene_buttons, self.camera.layout.ui_scale)

    def action_at_screen_position(self, position: tuple[int, int]) -> str | None:
        if self.ui_hidden:
            return None

        for button in [*self.control_buttons, *self.timeline_buttons, *self.scene_buttons]:
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
        elif action == "scene_system":
            self.camera.set_scene("full_system")
        elif action == "scene_inner":
            self.camera.set_scene("inner_worlds")
        elif action == "scene_outer":
            self.camera.set_scene("outer_worlds")
        elif action == "scene_focus" and self.selected_body is not None:
            self.camera.set_focus_body(self.selected_body)
        elif action.startswith("speed_"):
            self.simulation.set_time_speed_index(int(action.rsplit("_", 1)[1]))
        elif action == "reset":
            self.simulation.reset()
            self.camera.reset()
            self.paused = False
            self.selected_body = None
            self.panel_body = None
            self.panel_visibility = 0.0

    def handle_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_SPACE:
            self.handle_action("toggle_pause")
        elif event.key == pygame.K_o:
            self.handle_action("toggle_orbits")
        elif event.key == pygame.K_l:
            self.handle_action("toggle_labels")
        elif event.key == pygame.K_h:
            self.ui_hidden = not self.ui_hidden
        elif event.key == pygame.K_p:
            self.capture_screenshot()
        elif event.key == pygame.K_f and self.selected_body is not None:
            self.handle_action("scene_focus")
        elif event.key == pygame.K_1:
            self.handle_action("speed_0")
        elif event.key == pygame.K_2:
            self.handle_action("speed_1")
        elif event.key == pygame.K_3:
            self.handle_action("speed_2")
        elif event.key == pygame.K_4:
            self.handle_action("speed_3")
        elif event.key == pygame.K_q:
            self.handle_action("scene_system")
        elif event.key == pygame.K_w:
            self.handle_action("scene_inner")
        elif event.key == pygame.K_e:
            self.handle_action("scene_outer")

    def capture_screenshot(self) -> None:
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = screenshot_dir / f"gravity-studio-{timestamp}.png"
        pygame.image.save(self.screen, output_path)
        self.notification_text = f"Captured {output_path.name}"
        self.notification_timer = 2.0

    def draw_notification(self) -> None:
        if self.notification_text is None:
            return

        self.hud.draw_notification(self.screen, self.notification_text, self.notification_timer, self.camera.layout.ui_scale)

    def draw_intro_fade(self) -> None:
        if self.elapsed_time >= 2.2:
            return

        alpha = int(255 * max(0.0, 1.0 - self.elapsed_time / 2.2))
        fade = pygame.Surface(self.viewport, pygame.SRCALPHA)
        fade.fill((0, 0, 0, alpha))
        self.screen.blit(fade, (0, 0))

    def timeline_hit_test(self, position: tuple[int, int]) -> bool:
        if self.ui_hidden:
            return False

        return self.timeline_slider.track_rect.inflate(0, 18).collidepoint(position) or self.timeline_slider.handle_rect.collidepoint(position)

    def update_timeline_from_pointer(self, x_position: int) -> None:
        relative = (x_position - self.timeline_slider.track_rect.left) / max(1, self.timeline_slider.track_rect.width)
        clamped = max(0.0, min(1.0, relative))
        self.simulation.set_simulation_days(self.simulation.timeline_range_days * clamped)

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
