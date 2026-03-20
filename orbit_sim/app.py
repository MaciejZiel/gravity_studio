from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pygame
from pygame import Vector2

from orbit_sim.audio import AmbientSoundscape
from orbit_sim.background import StarField
from orbit_sim.branding import create_window_icon, draw_launch_splash
from orbit_sim.camera import SolarCamera
from orbit_sim.config import (
    FALLBACK_WINDOW_SIZE,
    SPACE_COLOR,
    TARGET_FPS,
)
from orbit_sim.models import CelestialBody
from orbit_sim.rendering import SceneRenderer
from orbit_sim.settings import StudioSettings, StudioSettingsStore
from orbit_sim.simulation import OrbitalSimulation
from orbit_sim.ui import ControlBar, DateShortcutStrip, FocusBadge, HudChrome, InfoPanel, SceneStrip, TimelineStrip


class GravityStudioApp:
    def __init__(self) -> None:
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("Gravity Studio: Solar System")
        pygame.display.set_icon(create_window_icon())
        self.settings_store = StudioSettingsStore(Path.cwd())
        self.settings = self.settings_store.load()
        self.viewport = self._detect_viewport()
        self.screen = self._create_display_surface()
        self.clock = pygame.time.Clock()
        self.camera = SolarCamera(self.viewport)
        if self.settings.scale_mode == "expanded":
            self.camera.toggle_scale_mode()
        self.camera.set_scene(self.settings.last_scene)
        self.star_field = StarField(self.viewport)
        self.simulation = OrbitalSimulation()
        self.soundscape = AmbientSoundscape(self.settings.master_volume)
        self.hud = HudChrome()
        self.info_panel = InfoPanel()
        self.focus_badge = FocusBadge()
        self.control_bar = ControlBar()
        self.scene_strip = SceneStrip()
        self.date_shortcuts = DateShortcutStrip()
        self.timeline_strip = TimelineStrip()
        self.scene_renderer = SceneRenderer()
        self.elapsed_time = 0.0
        self.hovered_body: CelestialBody | None = None
        self.selected_body: CelestialBody | None = None
        self.panel_body: CelestialBody | None = None
        self.panel_visibility = 0.0
        self.hovered_action: str | None = None
        self.show_orbits = self.settings.show_orbits
        self.show_labels = self.settings.show_labels
        self.ui_hidden = self.settings.ui_hidden
        self.notification_text: str | None = None
        self.notification_timer = 0.0
        self.focus_auto_rotation = 0.0
        self.focus_rotation_offset = 0.0
        self.dragging_focus_preview = False
        self.focus_drag_anchor_x = 0
        self.control_buttons = []
        self.timeline_buttons = []
        self.timeline_slider = self.timeline_strip.build_slider(
            *self.viewport,
            self.camera.layout.ui_scale,
            self.simulation.timeline_progress,
        )
        self.scene_buttons = []
        self.date_buttons = []
        self._ui_layout_key: tuple[object, ...] | None = None
        self.dragging_timeline = False
        self.paused = False
        self.running = True
        self._refresh_ui_layout(force=True)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.render()

        self.soundscape.shutdown()
        self.persist_settings()
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
                elif self.focus_preview_hit_test(event.pos):
                    self.dragging_focus_preview = True
                    self.focus_drag_anchor_x = event.pos[0]
                elif not self.ui_hidden and self.timeline_hit_test(event.pos):
                    self.dragging_timeline = True
                    self.update_timeline_from_pointer(event.pos[0])
                else:
                    previous_selection = self.selected_body
                    self.selected_body = self.body_at_screen_position(Vector2(event.pos))
                    if self.selected_body is not previous_selection:
                        self.focus_auto_rotation = 0.0
                        self.focus_rotation_offset = 0.0
                    self.camera.set_focus_body(self.selected_body)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_timeline = False
                self.dragging_focus_preview = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_focus_preview:
                    delta_x = event.pos[0] - self.focus_drag_anchor_x
                    self.focus_drag_anchor_x = event.pos[0]
                    self.focus_rotation_offset = (self.focus_rotation_offset + delta_x * 0.72) % 360.0
                elif self.dragging_timeline:
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
        self.soundscape.update(dt, self.camera.scene_mode == "focus", self.simulation.live_mode, self.ui_hidden)
        self._refresh_ui_layout()
        mouse_position = pygame.mouse.get_pos()
        self.hovered_action = self.action_at_screen_position(mouse_position)
        self.hovered_body = self.body_at_screen_position(Vector2(mouse_position))
        if self.selected_body is not None:
            self.focus_auto_rotation = (self.focus_auto_rotation + dt * self._focus_spin_rate(self.selected_body)) % 360.0
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
        local_now = datetime.now().astimezone()
        self.screen.fill(SPACE_COLOR)
        self.star_field.draw(self.screen, self.elapsed_time, self.camera.background_parallax)
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
            self.focus_auto_rotation + self.focus_rotation_offset,
        )
        if not self.ui_hidden:
            self.draw_hud(local_now)
            if self.camera.scene_mode != "focus":
                self.draw_info_panel()
            self.draw_focus_badge(local_now)
            self.draw_controls()
            if self.camera.scene_mode != "focus":
                self.draw_date_shortcuts()
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

    def draw_hud(self, local_now: datetime) -> None:
        self.hud.draw(
            self.screen,
            self.paused,
            self.simulation.live_mode,
            self.camera.zoom,
            self.camera.scale_mode,
            self.camera.scene_label,
            self.simulation.time_speed_label,
            local_now.strftime("%H:%M:%S"),
            local_now.strftime("%Z"),
            self.camera.layout.ui_scale,
        )

    def draw_focus_badge(self, local_now: datetime) -> None:
        if self.selected_body is None or not self.should_draw_focus_badge():
            return

        self.focus_badge.draw(
            self.screen,
            self.selected_body,
            local_now.strftime("%H:%M:%S"),
            self.simulation.current_datetime().strftime("%H:%M:%S"),
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

    def draw_date_shortcuts(self) -> None:
        self.date_shortcuts.draw(self.screen, self.date_buttons, self.camera.layout.ui_scale)

    def action_at_screen_position(self, position: tuple[int, int]) -> str | None:
        if self.ui_hidden:
            return None

        buttons = [*self.control_buttons, *self.scene_buttons]
        if self.camera.scene_mode != "focus":
            buttons.extend(self.timeline_buttons)
            buttons.extend(self.date_buttons)

        for button in buttons:
            if button.rect.collidepoint(position):
                return button.action

        return None

    def handle_action(self, action: str) -> None:
        if action == "toggle_pause":
            self.paused = not self.paused
        elif action == "toggle_live":
            self.simulation.set_live_mode(not self.simulation.live_mode)
            if self.simulation.live_mode:
                self.paused = False
        elif action == "toggle_orbits":
            self.show_orbits = not self.show_orbits
        elif action == "toggle_labels":
            self.show_labels = not self.show_labels
        elif action == "toggle_sound":
            enabled = self.settings.master_volume == 0.0
            self.settings.master_volume = 0.42 if enabled else 0.0
            self.soundscape.set_enabled(enabled, self.settings.master_volume)
        elif action == "toggle_scale":
            self.camera.toggle_scale_mode()
        elif action == "scene_system":
            self.camera.set_scene("full_system")
        elif action == "scene_inner":
            self.camera.set_scene("inner_worlds")
        elif action == "scene_giants":
            self.camera.set_scene("gas_giants")
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
            self.focus_auto_rotation = 0.0
            self.focus_rotation_offset = 0.0
        elif action == "capture_clean":
            self.capture_screenshot(clean=True)
        elif action.startswith("jump_"):
            self.simulation.jump_to_bookmark(action)
            if action == "jump_now":
                self.paused = False
        self.persist_settings()

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
        elif event.key == pygame.K_g:
            self.handle_action("scene_giants")
        elif event.key == pygame.K_e:
            self.handle_action("scene_outer")

    def capture_screenshot(self, clean: bool = False) -> None:
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = "-clean" if clean else ""
        output_path = screenshot_dir / f"gravity-studio-{timestamp}{suffix}.png"
        if clean:
            capture_surface = self._render_capture_surface()
            pygame.image.save(capture_surface, output_path)
        else:
            pygame.image.save(self.screen, output_path)
        self.notification_text = f"Captured {output_path.name}"
        self.notification_timer = 2.0

    def draw_notification(self) -> None:
        if self.notification_text is None:
            return

        self.hud.draw_notification(self.screen, self.notification_text, self.notification_timer, self.camera.layout.ui_scale)

    def draw_intro_fade(self) -> None:
        draw_launch_splash(self.screen, self.elapsed_time, self.camera.layout.ui_scale)

    def timeline_hit_test(self, position: tuple[int, int]) -> bool:
        if self.ui_hidden or self.camera.scene_mode == "focus":
            return False

        return self.timeline_slider.track_rect.inflate(0, 18).collidepoint(position) or self.timeline_slider.handle_rect.collidepoint(position)

    def focus_preview_hit_test(self, position: tuple[int, int]) -> bool:
        if self.selected_body is None:
            return False

        preview_rect = self.scene_renderer.focus_closeup_rect(self.viewport, self.camera)
        if preview_rect is None or not preview_rect.collidepoint(position):
            return False

        center = Vector2(preview_rect.center)
        radius = preview_rect.width / 2
        return Vector2(position).distance_to(center) <= radius

    def update_timeline_from_pointer(self, x_position: int) -> None:
        relative = (x_position - self.timeline_slider.track_rect.left) / max(1, self.timeline_slider.track_rect.width)
        clamped = max(0.0, min(1.0, relative))
        self.simulation.set_live_mode(False)
        self.simulation.set_timeline_progress(clamped)

    def should_draw_focus_badge(self) -> bool:
        return self.camera.scene_mode == "focus" or self.camera.zoom >= 1.65

    def active_jump_action(self) -> str | None:
        if self.simulation.live_mode:
            return "jump_now"

        current = self.simulation.current_datetime()
        for bookmark in self.simulation.bookmarks()[1:]:
            if abs((bookmark.moment - current).total_seconds()) <= 3600 * 12:
                return bookmark.action
        return None

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

    def _render_capture_surface(self) -> pygame.Surface:
        capture_surface = pygame.Surface(self.viewport)
        capture_surface.fill(SPACE_COLOR)
        self.star_field.draw(capture_surface, self.elapsed_time, self.camera.background_parallax)
        self.scene_renderer.draw(
            capture_surface,
            self.camera,
            self.simulation.bodies,
            self.elapsed_time,
            self.simulation.simulation_days,
            self.hovered_body,
            self.selected_body,
            self.show_orbits,
            self.show_labels,
            self.focus_auto_rotation + self.focus_rotation_offset,
        )
        return capture_surface

    def persist_settings(self) -> None:
        self.settings = StudioSettings(
            show_orbits=self.show_orbits,
            show_labels=self.show_labels,
            scale_mode=self.camera.scale_mode,
            last_scene=self.camera.scene_mode,
            ui_hidden=self.ui_hidden,
            master_volume=self.settings.master_volume,
        )
        self.settings_store.save(self.settings)

    def _focus_spin_rate(self, body: CelestialBody) -> float:
        rotation_hours = max(4.0, abs(body.rotation_hours))
        relative_speed = (24.0 / rotation_hours) ** 0.45
        return max(4.0, min(18.0, 5.5 * relative_speed))

    def _refresh_ui_layout(self, force: bool = False) -> None:
        layout_key = (
            self.viewport,
            round(self.camera.layout.ui_scale, 3),
            self.paused,
            self.simulation.live_mode,
            self.settings.master_volume > 0.0,
            self.show_orbits,
            self.show_labels,
            self.camera.scale_mode,
            self.camera.scene_mode,
            self.simulation.time_speed_index,
            round(self.simulation.timeline_progress, 5),
            self.selected_body is not None,
            self.active_jump_action(),
        )
        if not force and layout_key == self._ui_layout_key:
            return

        self._ui_layout_key = layout_key
        ui_scale = self.camera.layout.ui_scale
        self.control_buttons = self.control_bar.build_buttons(
            *self.viewport,
            ui_scale,
            paused=self.paused,
            live_mode=self.simulation.live_mode,
            sound_enabled=self.settings.master_volume > 0.0,
            show_orbits=self.show_orbits,
            show_labels=self.show_labels,
            scale_mode=self.camera.scale_mode,
            focus_mode=self.camera.scene_mode == "focus",
        )
        self.timeline_buttons = self.timeline_strip.build_speed_buttons(
            *self.viewport,
            ui_scale,
            self.simulation.time_speed_index,
            self.simulation.live_mode,
        )
        self.timeline_slider = self.timeline_strip.build_slider(
            *self.viewport,
            ui_scale,
            self.simulation.timeline_progress,
        )
        self.scene_buttons = self.scene_strip.build_buttons(
            self.viewport[0],
            ui_scale,
            self.camera.scene_mode,
            self.selected_body is not None,
        )
        self.date_buttons = self.date_shortcuts.build_buttons(
            *self.viewport,
            ui_scale,
            self.active_jump_action(),
        )
