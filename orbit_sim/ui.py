from __future__ import annotations

from dataclasses import dataclass

import pygame
from pygame import Vector2

from orbit_sim.models import CelestialBody
from orbit_sim.simulation import TimelineBookmark


@dataclass
class ControlButton:
    action: str
    label: str
    rect: pygame.Rect
    active: bool = False


@dataclass
class SliderControl:
    action: str
    track_rect: pygame.Rect
    handle_rect: pygame.Rect
    value: float


def render_cached(
    cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface],
    font: pygame.font.Font,
    text: str,
    color: tuple[int, ...],
) -> pygame.Surface:
    key = (id(font), text, color)
    if key not in cache:
        cache[key] = font.render(text, True, color)
    return cache[key]


class InfoPanel:
    def __init__(self) -> None:
        self.scale = 0.0
        self.eyebrow_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.label_font: pygame.font.Font | None = None
        self.value_font: pygame.font.Font | None = None
        self.fact_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def draw(self, surface: pygame.Surface, body: CelestialBody, visibility: float, ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        panel_width = int(380 * ui_scale)
        panel_height = int(354 * ui_scale)
        slide = int((1.0 - visibility) * 20 * ui_scale)
        alpha = max(0, min(255, int(visibility * 255)))
        x = surface.get_width() - panel_width - int(40 * ui_scale) + slide
        y = int(34 * ui_scale)

        shadow = pygame.Surface((panel_width + 24, panel_height + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, int(alpha * 0.28)), shadow.get_rect(), border_radius=int(26 * ui_scale))
        surface.blit(shadow, (x - int(10 * ui_scale), y + int(10 * ui_scale)))

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (9, 12, 19, int(alpha * 0.93)), panel.get_rect(), border_radius=int(22 * ui_scale))
        pygame.draw.rect(panel, (48, 56, 70, int(alpha * 0.9)), panel.get_rect(), width=1, border_radius=int(22 * ui_scale))

        pygame.draw.circle(panel, (*body.color, int(alpha * 0.92)), (int(34 * ui_scale), int(34 * ui_scale)), max(5, int(8 * ui_scale)))
        eyebrow = render_cached(self._text_cache, self.eyebrow_font, "SELECTED PLANET", (150, 160, 178))
        title = render_cached(self._text_cache, self.title_font, body.name, (234, 238, 244))
        panel.blit(eyebrow, (int(56 * ui_scale), int(22 * ui_scale)))
        panel.blit(title, (int(24 * ui_scale), int(48 * ui_scale)))

        rows = [
            ("Radius", f"{body.radius_km:,.0f} km"),
            ("Distance", f"{body.distance_au:.2f} AU"),
            ("Orbital period", self._format_period(body.orbital_period_days)),
        ]
        top = int(120 * ui_scale)
        row_gap = int(42 * ui_scale)
        for label, value in rows:
            self._draw_stat_row(panel, label, value, top, ui_scale)
            top += row_gap

        comparison_title = render_cached(self._text_cache, self.label_font, "Compared with Earth", (132, 142, 160))
        comparison_value = render_cached(self._text_cache, self.fact_font, self._comparison_text(body), (208, 214, 224))
        panel.blit(comparison_title, (int(24 * ui_scale), int(248 * ui_scale)))
        panel.blit(comparison_value, (int(24 * ui_scale), int(268 * ui_scale)))

        fact_title = render_cached(self._text_cache, self.label_font, "Fact", (132, 142, 160))
        panel.blit(fact_title, (int(24 * ui_scale), int(298 * ui_scale)))
        fact_lines = self._wrap_text(body.fact, self.fact_font, panel_width - int(48 * ui_scale))
        text_y = int(318 * ui_scale)
        for line in fact_lines[:2]:
            line_surface = render_cached(self._text_cache, self.fact_font, line, (208, 214, 224))
            panel.blit(line_surface, (int(24 * ui_scale), text_y))
            text_y += int(19 * ui_scale)

        surface.blit(panel, (x, y))

    def _draw_stat_row(self, panel: pygame.Surface, label: str, value: str, top: int, ui_scale: float) -> None:
        pygame.draw.line(
            panel,
            (36, 43, 54, 220),
            (int(24 * ui_scale), top - int(10 * ui_scale)),
            (panel.get_width() - int(24 * ui_scale), top - int(10 * ui_scale)),
            1,
        )
        label_surface = render_cached(self._text_cache, self.label_font, label, (132, 142, 160))
        value_surface = render_cached(self._text_cache, self.value_font, value, (226, 231, 238))
        panel.blit(label_surface, (int(24 * ui_scale), top))
        panel.blit(value_surface, (panel.get_width() - value_surface.get_width() - int(24 * ui_scale), top - int(2 * ui_scale)))

    def _format_period(self, orbital_period_days: float) -> str:
        if orbital_period_days >= 730:
            return f"{orbital_period_days / 365.25:.1f} years"
        return f"{orbital_period_days:.0f} days"

    def _wrap_text(self, text: str, font: pygame.font.Font, width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []

        for word in words:
            candidate = " ".join(current + [word])
            if current and font.size(candidate)[0] > width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)

        if current:
            lines.append(" ".join(current))

        return lines

    def _comparison_text(self, body: CelestialBody) -> str:
        if body.name == "Earth":
            return "Baseline reference for size and year length."

        radius_ratio = body.radius_km / 6371.0
        year_ratio = body.orbital_period_days / 365.25
        return f"{radius_ratio:.1f}x radius, {year_ratio:.1f}x year length"

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.eyebrow_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)), bold=True)
        self.title_font = pygame.font.SysFont("segoeui", max(18, int(28 * ui_scale)), bold=True)
        self.label_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)))
        self.value_font = pygame.font.SysFont("segoeui", max(14, int(17 * ui_scale)))
        self.fact_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)))


class HudChrome:
    def __init__(self) -> None:
        self.scale = 0.0
        self.title_font: pygame.font.Font | None = None
        self.subtitle_font: pygame.font.Font | None = None
        self.meta_font: pygame.font.Font | None = None
        self.note_font: pygame.font.Font | None = None
        self.clock_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def draw(
        self,
        surface: pygame.Surface,
        paused: bool,
        live_mode: bool,
        zoom: float,
        scale_mode: str,
        scene_label: str,
        time_speed_label: str,
        local_time_label: str,
        timezone_label: str,
        ui_scale: float,
    ) -> None:
        self._ensure_fonts(ui_scale)
        margin_x = int(42 * ui_scale)
        title = render_cached(self._text_cache, self.title_font, "SOLAR SYSTEM", (230, 235, 242))
        subtitle = render_cached(
            self._text_cache,
            self.subtitle_font,
            "Astronomy-inspired orbital visualization",
            (124, 136, 156),
        )
        status_label = "PAUSED" if paused else ("REAL-TIME" if live_mode else "SIMULATING")
        meta = render_cached(
            self._text_cache,
            self.meta_font,
            f"{status_label}   |   {scene_label.upper()}   |   {time_speed_label}   |   ZOOM {int(zoom * 100)}%   |   SCALE {scale_mode.upper()}",
            (106, 118, 140),
        )
        hint = render_cached(
            self._text_cache,
            self.meta_font,
            "Q/W/E/G scenes, T/Y tours, D presentation, M missions, K sky, S story scale.",
            (88, 100, 120),
        )

        surface.blit(title, (margin_x, int(34 * ui_scale)))
        surface.blit(subtitle, (margin_x, int(70 * ui_scale)))
        surface.blit(meta, (margin_x, int(102 * ui_scale)))
        surface.blit(hint, (margin_x, int(124 * ui_scale)))
        self._draw_clock_badge(surface, local_time_label, timezone_label, ui_scale)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.title_font = pygame.font.SysFont("segoeui", max(20, int(28 * ui_scale)), bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", max(13, int(15 * ui_scale)))
        self.meta_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
        self.note_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)), bold=True)
        self.clock_font = pygame.font.SysFont("segoeui", max(16, int(20 * ui_scale)), bold=True)

    def draw_notification(self, surface: pygame.Surface, text: str, timer: float, ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        alpha = max(0, min(255, int(255 * min(1.0, timer))))
        label_surface = render_cached(self._text_cache, self.note_font, text, (230, 235, 242))
        padding_x = int(18 * ui_scale)
        padding_y = int(12 * ui_scale)
        width = label_surface.get_width() + padding_x * 2
        height = label_surface.get_height() + padding_y * 2
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 14, 22, int(alpha * 0.92)), panel.get_rect(), border_radius=int(16 * ui_scale))
        pygame.draw.rect(panel, (66, 74, 88, int(alpha * 0.95)), panel.get_rect(), width=1, border_radius=int(16 * ui_scale))
        panel.blit(label_surface, (padding_x, padding_y))
        surface.blit(panel, (surface.get_width() - width - int(36 * ui_scale), surface.get_height() - height - int(32 * ui_scale)))

    def _draw_clock_badge(
        self,
        surface: pygame.Surface,
        local_time_label: str,
        timezone_label: str,
        ui_scale: float,
    ) -> None:
        badge_width = int(184 * ui_scale)
        badge_height = int(68 * ui_scale)
        badge = pygame.Surface((badge_width, badge_height), pygame.SRCALPHA)
        pygame.draw.rect(badge, (8, 12, 19, 214), badge.get_rect(), border_radius=int(18 * ui_scale))
        pygame.draw.rect(badge, (48, 56, 68, 222), badge.get_rect(), width=1, border_radius=int(18 * ui_scale))

        label = render_cached(self._text_cache, self.meta_font, "LOCAL CLOCK", (124, 136, 156))
        value = render_cached(self._text_cache, self.clock_font, local_time_label, (232, 236, 241))
        timezone = render_cached(self._text_cache, self.meta_font, timezone_label, (110, 120, 138))
        badge.blit(label, (int(16 * ui_scale), int(12 * ui_scale)))
        badge.blit(value, (int(16 * ui_scale), int(28 * ui_scale)))
        badge.blit(timezone, (badge_width - timezone.get_width() - int(16 * ui_scale), int(14 * ui_scale)))
        surface.blit(badge, (int(42 * ui_scale), int(154 * ui_scale)))


class FocusBadge:
    def __init__(self) -> None:
        self.scale = 0.0
        self.eyebrow_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.label_font: pygame.font.Font | None = None
        self.value_font: pygame.font.Font | None = None
        self.meta_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def draw(
        self,
        surface: pygame.Surface,
        body: CelestialBody,
        local_time_label: str,
        simulation_time_label: str,
        ui_scale: float,
    ) -> None:
        self._ensure_fonts(ui_scale)
        panel_width = int(296 * ui_scale)
        panel_height = int(196 * ui_scale)
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 19, 224), panel.get_rect(), border_radius=int(22 * ui_scale))
        pygame.draw.rect(panel, (50, 58, 72, 228), panel.get_rect(), width=1, border_radius=int(22 * ui_scale))

        eyebrow = render_cached(self._text_cache, self.eyebrow_font, "LIVE CLOSE-UP", (138, 148, 166))
        title = render_cached(self._text_cache, self.title_font, body.name, (232, 236, 242))
        panel.blit(eyebrow, (int(20 * ui_scale), int(18 * ui_scale)))
        panel.blit(title, (int(20 * ui_scale), int(38 * ui_scale)))

        rows = [
            ("Local", local_time_label),
            ("Sim", simulation_time_label),
            ("Radius", f"{body.radius_km:,.0f} km"),
            ("Period", self._format_period(body.orbital_period_days)),
        ]
        top = int(74 * ui_scale)
        for label, value in rows:
            self._draw_time_row(panel, label, value, top, ui_scale)
            top += int(24 * ui_scale)

        hint = render_cached(self._text_cache, self.meta_font, "Drag sphere to rotate", (112, 124, 144))
        panel.blit(hint, (int(20 * ui_scale), int(170 * ui_scale)))

        x = int(42 * ui_scale)
        y = int(surface.get_height() * 0.66)
        surface.blit(panel, (x, y))

    def _draw_time_row(self, panel: pygame.Surface, label: str, value: str, top: int, ui_scale: float) -> None:
        label_surface = render_cached(self._text_cache, self.label_font, label, (128, 138, 156))
        value_surface = render_cached(self._text_cache, self.value_font, value, (222, 228, 236))
        panel.blit(label_surface, (int(20 * ui_scale), top))
        panel.blit(value_surface, (panel.get_width() - value_surface.get_width() - int(20 * ui_scale), top - int(1 * ui_scale)))

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.eyebrow_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.title_font = pygame.font.SysFont("segoeui", max(20, int(24 * ui_scale)), bold=True)
        self.label_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
        self.value_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)))
        self.meta_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)))

    def _format_period(self, orbital_period_days: float) -> str:
        if orbital_period_days >= 730:
            return f"{orbital_period_days / 365.25:.1f} years"
        return f"{orbital_period_days:.0f} days"


class ControlBar:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def build_buttons(
        self,
        width: int,
        height: int,
        ui_scale: float,
        paused: bool,
        live_mode: bool,
        sound_enabled: bool,
        show_orbits: bool,
        show_labels: bool,
        show_missions: bool,
        show_sky: bool,
        story_mode: bool,
        scale_mode: str,
        focus_mode: bool,
    ) -> list[ControlButton]:
        self._ensure_fonts(ui_scale)
        if focus_mode:
            labels = [
                ("scene_system", "Back", False),
                ("toggle_live", "Live", live_mode),
                ("toggle_pause", "Resume" if paused else "Pause", paused),
                ("toggle_sound", "Sound", sound_enabled),
                ("toggle_missions", "Missions", show_missions),
                ("toggle_sky", "Sky", show_sky),
                ("toggle_story_scale", "Story Scale", story_mode),
                ("capture_clean", "Clean Shot", False),
                ("reset", "Reset", False),
            ]
        else:
            labels = [
                ("toggle_live", "Live", live_mode),
                ("toggle_pause", "Resume" if paused else "Pause", paused),
                ("toggle_sound", "Sound", sound_enabled),
                ("toggle_orbits", "Orbits", show_orbits),
                ("toggle_labels", "Labels", show_labels),
                ("toggle_missions", "Missions", show_missions),
                ("toggle_sky", "Sky", show_sky),
                ("toggle_story_scale", "Story Scale", story_mode),
                ("toggle_scale", f"Scale: {scale_mode.title()}", scale_mode == "expanded"),
                ("reset", "Reset", False),
            ]
        margin_x = int(38 * ui_scale)
        y = height - int(82 * ui_scale)
        gap = int(10 * ui_scale)
        height_px = int(42 * ui_scale)
        buttons: list[ControlButton] = []
        x = margin_x

        for action, label, active in labels:
            button_width = max(int(82 * ui_scale), self.button_font.size(label)[0] + int(28 * ui_scale))
            rect = pygame.Rect(x, y, button_width, height_px)
            buttons.append(ControlButton(action=action, label=label, rect=rect, active=active))
            x += button_width + gap

        return buttons

    def draw(
        self,
        surface: pygame.Surface,
        buttons: list[ControlButton],
        hovered_action: str | None,
        ui_scale: float,
    ) -> None:
        self._ensure_fonts(ui_scale)
        if not buttons:
            return

        bar_rect = buttons[0].rect.unionall([button.rect for button in buttons[1:]]).inflate(int(16 * ui_scale), int(16 * ui_scale))
        shadow = pygame.Surface((bar_rect.width + int(20 * ui_scale), bar_rect.height + int(20 * ui_scale)), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 64), shadow.get_rect(), border_radius=int(24 * ui_scale))
        surface.blit(shadow, (bar_rect.x - int(10 * ui_scale), bar_rect.y + int(8 * ui_scale)))

        tray = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(tray, (8, 11, 18, 214), tray.get_rect(), border_radius=int(20 * ui_scale))
        pygame.draw.rect(tray, (42, 48, 60, 220), tray.get_rect(), width=1, border_radius=int(20 * ui_scale))
        surface.blit(tray, bar_rect.topleft)

        for button in buttons:
            fill = (14, 18, 26, 250)
            border = (49, 56, 70, 255)
            text_color = (214, 220, 230)

            if button.active:
                fill = (25, 33, 46, 252)
                border = (108, 124, 148, 255)
            elif button.action == hovered_action:
                fill = (19, 25, 36, 252)
                border = (78, 90, 110, 255)

            button_surface = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(button_surface, fill, button_surface.get_rect(), border_radius=int(14 * ui_scale))
            pygame.draw.rect(button_surface, border, button_surface.get_rect(), width=1, border_radius=int(14 * ui_scale))
            label_surface = render_cached(self._text_cache, self.button_font, button.label, text_color)
            label_rect = label_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label_surface, label_rect)
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.button_font = pygame.font.SysFont("segoeui", max(12, int(14 * ui_scale)), bold=True)


class SceneStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def build_buttons(
        self,
        width: int,
        ui_scale: float,
        current_scene: str,
        has_selection: bool,
    ) -> list[ControlButton]:
        self._ensure_fonts(ui_scale)
        labels = [
            ("scene_system", "System", current_scene == "full_system"),
            ("scene_inner", "Inner", current_scene == "inner_worlds"),
            ("scene_giants", "Giants", current_scene == "gas_giants"),
            ("scene_outer", "Outer", current_scene == "outer_worlds"),
            ("scene_focus", "Focus", current_scene == "focus" and has_selection),
        ]
        x = width - int(36 * ui_scale)
        y = int(34 * ui_scale)
        gap = int(8 * ui_scale)
        buttons: list[ControlButton] = []

        for action, label, active in reversed(labels):
            button_width = max(int(68 * ui_scale), self.button_font.size(label)[0] + int(24 * ui_scale))
            rect = pygame.Rect(x - button_width, y, button_width, int(32 * ui_scale))
            buttons.append(ControlButton(action=action, label=label, rect=rect, active=active))
            x -= button_width + gap

        buttons.reverse()
        return buttons

    def draw(self, surface: pygame.Surface, buttons: list[ControlButton], ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        for button in buttons:
            fill = (10, 14, 22, 214)
            border = (50, 58, 72, 230)
            if button.active:
                fill = (26, 34, 46, 240)
                border = (120, 132, 156, 240)

            button_surface = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(button_surface, fill, button_surface.get_rect(), border_radius=int(14 * ui_scale))
            pygame.draw.rect(button_surface, border, button_surface.get_rect(), width=1, border_radius=int(14 * ui_scale))
            label_surface = render_cached(self._text_cache, self.button_font, button.label, (224, 229, 237))
            label_rect = label_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label_surface, label_rect)
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.button_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)), bold=True)


class TourStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def build_buttons(
        self,
        width: int,
        ui_scale: float,
        active_action: str | None,
        presentation_mode: bool,
    ) -> list[ControlButton]:
        self._ensure_fonts(ui_scale)
        labels = [
            ("tour_grand", "Grand Tour", active_action == "tour_grand"),
            ("tour_history", "History", active_action == "tour_history"),
            ("toggle_presentation", "Presentation", presentation_mode),
        ]
        x = width - int(36 * ui_scale)
        y = int(74 * ui_scale)
        gap = int(8 * ui_scale)
        buttons: list[ControlButton] = []
        for action, label, active in reversed(labels):
            button_width = max(int(94 * ui_scale), self.button_font.size(label)[0] + int(24 * ui_scale))
            rect = pygame.Rect(x - button_width, y, button_width, int(32 * ui_scale))
            buttons.append(ControlButton(action=action, label=label, rect=rect, active=active))
            x -= button_width + gap
        buttons.reverse()
        return buttons

    def draw(self, surface: pygame.Surface, buttons: list[ControlButton], ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        for button in buttons:
            fill = (9, 13, 21, 214)
            border = (46, 54, 68, 230)
            if button.active:
                fill = (28, 38, 52, 240)
                border = (124, 138, 164, 240)
            button_surface = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(button_surface, fill, button_surface.get_rect(), border_radius=int(14 * ui_scale))
            pygame.draw.rect(button_surface, border, button_surface.get_rect(), width=1, border_radius=int(14 * ui_scale))
            label_surface = render_cached(self._text_cache, self.button_font, button.label, (228, 232, 240))
            button_surface.blit(label_surface, label_surface.get_rect(center=button_surface.get_rect().center))
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return
        self.scale = ui_scale
        self._text_cache.clear()
        self.button_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)), bold=True)


class DateShortcutStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None
        self.label_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def build_buttons(
        self,
        width: int,
        height: int,
        ui_scale: float,
        bookmarks: list[TimelineBookmark],
        active_action: str | None,
    ) -> list[ControlButton]:
        self._ensure_fonts(ui_scale)
        labels = [(bookmark.action, bookmark.label) for bookmark in bookmarks]
        y = height - int(170 * ui_scale)
        gap = int(8 * ui_scale)
        widths = [max(int(70 * ui_scale), self.button_font.size(label)[0] + int(24 * ui_scale)) for _, label in labels]
        total_width = sum(widths) + gap * max(0, len(widths) - 1)
        x = max(int(42 * ui_scale), (width - total_width) // 2)
        buttons: list[ControlButton] = []
        for (action, label), button_width in zip(labels, widths):
            rect = pygame.Rect(x, y, button_width, int(28 * ui_scale))
            buttons.append(ControlButton(action=action, label=label, rect=rect, active=action == active_action))
            x += button_width + gap
        return buttons

    def draw(self, surface: pygame.Surface, buttons: list[ControlButton], ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        if not buttons:
            return

        label = render_cached(self._text_cache, self.label_font, "QUICK DATES", (118, 128, 146))
        surface.blit(label, (buttons[0].rect.x, buttons[0].rect.y - int(18 * ui_scale)))
        for button in buttons:
            fill = (9, 12, 19, 210)
            border = (48, 56, 72, 220)
            if button.active:
                fill = (24, 34, 46, 244)
                border = (112, 126, 148, 240)

            chip = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(chip, fill, chip.get_rect(), border_radius=int(12 * ui_scale))
            pygame.draw.rect(chip, border, chip.get_rect(), width=1, border_radius=int(12 * ui_scale))
            text = render_cached(self._text_cache, self.button_font, button.label, (220, 226, 234))
            chip.blit(text, text.get_rect(center=chip.get_rect().center))
            surface.blit(chip, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.button_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.label_font = pygame.font.SysFont("segoeui", max(9, int(10 * ui_scale)), bold=True)


class TimelineStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.label_font: pygame.font.Font | None = None
        self.meta_font: pygame.font.Font | None = None
        self.speed_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def build_speed_buttons(
        self,
        width: int,
        height: int,
        ui_scale: float,
        time_speed_index: int,
        live_mode: bool,
    ) -> list[ControlButton]:
        self._ensure_fonts(ui_scale)
        panel_width = min(int(width * 0.42), int(760 * ui_scale))
        panel_x = (width - panel_width) // 2
        y = height - int(122 * ui_scale)
        gap = int(8 * ui_scale)
        labels = ["1x", "10x", "100x", "1000x"]
        buttons: list[ControlButton] = []
        x = panel_x + panel_width - int(24 * ui_scale)

        for index, label in reversed(list(enumerate(labels))):
            button_width = max(int(56 * ui_scale), self.speed_font.size(label)[0] + int(24 * ui_scale))
            rect = pygame.Rect(x - button_width, y, button_width, int(30 * ui_scale))
            buttons.append(ControlButton(action=f"speed_{index}", label=label, rect=rect, active=(not live_mode and index == time_speed_index)))
            x -= button_width + gap

        buttons.reverse()
        return buttons

    def build_slider(
        self,
        width: int,
        height: int,
        ui_scale: float,
        value: float,
    ) -> SliderControl:
        panel_width = min(int(width * 0.42), int(760 * ui_scale))
        track_width = panel_width - int(40 * ui_scale)
        track_height = max(4, int(6 * ui_scale))
        track_rect = pygame.Rect((width - track_width) // 2, height - int(76 * ui_scale), track_width, track_height)
        handle_x = track_rect.x + int(track_rect.width * value)
        handle_rect = pygame.Rect(0, 0, int(16 * ui_scale), int(16 * ui_scale))
        handle_rect.center = (handle_x, track_rect.centery)
        return SliderControl(action="timeline", track_rect=track_rect, handle_rect=handle_rect, value=value)

    def draw(
        self,
        surface: pygame.Surface,
        speed_buttons: list[ControlButton],
        slider: SliderControl,
        date_label: str,
        ui_scale: float,
    ) -> None:
        self._ensure_fonts(ui_scale)
        panel_rect = slider.track_rect.inflate(int(40 * ui_scale), int(86 * ui_scale))
        panel_rect.y -= int(18 * ui_scale)

        shadow = pygame.Surface((panel_rect.width + int(20 * ui_scale), panel_rect.height + int(22 * ui_scale)), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 56), shadow.get_rect(), border_radius=int(24 * ui_scale))
        surface.blit(shadow, (panel_rect.x - int(10 * ui_scale), panel_rect.y + int(8 * ui_scale)))

        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 11, 18, 220), panel.get_rect(), border_radius=int(22 * ui_scale))
        pygame.draw.rect(panel, (42, 48, 60, 220), panel.get_rect(), width=1, border_radius=int(22 * ui_scale))
        surface.blit(panel, panel_rect.topleft)

        label_surface = render_cached(self._text_cache, self.label_font, "SIMULATION TIME", (126, 136, 154))
        value_surface = render_cached(self._text_cache, self.meta_font, date_label, (228, 233, 240))
        surface.blit(label_surface, (panel_rect.x + int(20 * ui_scale), panel_rect.y + int(16 * ui_scale)))
        surface.blit(value_surface, (panel_rect.x + int(20 * ui_scale), panel_rect.y + int(36 * ui_scale)))

        track_surface = pygame.Surface(slider.track_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(track_surface, (36, 43, 56, 255), track_surface.get_rect(), border_radius=track_surface.get_height() // 2)
        filled_rect = track_surface.get_rect()
        filled_rect.width = max(1, int(track_surface.get_width() * slider.value))
        pygame.draw.rect(track_surface, (120, 132, 158, 255), filled_rect, border_radius=track_surface.get_height() // 2)
        surface.blit(track_surface, slider.track_rect.topleft)

        handle_surface = pygame.Surface(slider.handle_rect.size, pygame.SRCALPHA)
        pygame.draw.circle(handle_surface, (228, 232, 239), handle_surface.get_rect().center, handle_surface.get_width() // 2)
        pygame.draw.circle(handle_surface, (64, 74, 92), handle_surface.get_rect().center, max(1, handle_surface.get_width() // 2 - 1), 1)
        surface.blit(handle_surface, slider.handle_rect.topleft)

        for button in speed_buttons:
            fill = (14, 18, 26, 250)
            border = (49, 56, 70, 255)
            if button.active:
                fill = (26, 34, 46, 252)
                border = (112, 126, 148, 255)

            button_surface = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(button_surface, fill, button_surface.get_rect(), border_radius=int(12 * ui_scale))
            pygame.draw.rect(button_surface, border, button_surface.get_rect(), width=1, border_radius=int(12 * ui_scale))
            label = render_cached(self._text_cache, self.speed_font, button.label, (220, 226, 234))
            label_rect = label.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label, label_rect)
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self._text_cache.clear()
        self.label_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.meta_font = pygame.font.SysFont("segoeui", max(13, int(15 * ui_scale)))
        self.speed_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)), bold=True)


class TourCaption:
    def __init__(self) -> None:
        self.scale = 0.0
        self.eyebrow_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.body_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def draw(
        self,
        surface: pygame.Surface,
        title: str,
        caption: str,
        progress: float,
        ui_scale: float,
    ) -> None:
        self._ensure_fonts(ui_scale)
        panel_width = int(min(surface.get_width() * 0.42, 660 * ui_scale))
        panel_height = int(122 * ui_scale)
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 20, 220), panel.get_rect(), border_radius=int(20 * ui_scale))
        pygame.draw.rect(panel, (50, 60, 76, 230), panel.get_rect(), width=1, border_radius=int(20 * ui_scale))
        eyebrow = render_cached(self._text_cache, self.eyebrow_font, "CINEMATIC TOUR", (132, 142, 160))
        title_surface = render_cached(self._text_cache, self.title_font, title, (232, 237, 244))
        body_surface = render_cached(self._text_cache, self.body_font, caption, (196, 204, 216))
        panel.blit(eyebrow, (int(22 * ui_scale), int(18 * ui_scale)))
        panel.blit(title_surface, (int(22 * ui_scale), int(40 * ui_scale)))
        panel.blit(body_surface, (int(22 * ui_scale), int(70 * ui_scale)))
        track_rect = pygame.Rect(int(22 * ui_scale), panel_height - int(18 * ui_scale), panel_width - int(44 * ui_scale), max(4, int(6 * ui_scale)))
        pygame.draw.rect(panel, (34, 42, 56), track_rect, border_radius=track_rect.height // 2)
        fill_rect = track_rect.copy()
        fill_rect.width = max(8, int(track_rect.width * progress))
        pygame.draw.rect(panel, (132, 156, 188), fill_rect, border_radius=track_rect.height // 2)
        surface.blit(panel, (surface.get_width() // 2 - panel_width // 2, surface.get_height() - panel_height - int(38 * ui_scale)))

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return
        self.scale = ui_scale
        self._text_cache.clear()
        self.eyebrow_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.title_font = pygame.font.SysFont("segoeui", max(18, int(24 * ui_scale)), bold=True)
        self.body_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)))


class EventHighlight:
    def __init__(self) -> None:
        self.scale = 0.0
        self.eyebrow_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.body_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def draw(self, surface: pygame.Surface, bookmark: TimelineBookmark, ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        panel_width = int(420 * ui_scale)
        panel_height = int(88 * ui_scale)
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 19, 214), panel.get_rect(), border_radius=int(18 * ui_scale))
        pygame.draw.rect(panel, (52, 58, 72, 224), panel.get_rect(), width=1, border_radius=int(18 * ui_scale))
        eyebrow = render_cached(self._text_cache, self.eyebrow_font, "ASTRONOMY EVENT", (126, 138, 156))
        title = render_cached(self._text_cache, self.title_font, bookmark.label, (230, 236, 242))
        body = render_cached(self._text_cache, self.body_font, bookmark.description, (190, 198, 210))
        panel.blit(eyebrow, (int(18 * ui_scale), int(12 * ui_scale)))
        panel.blit(title, (int(18 * ui_scale), int(30 * ui_scale)))
        panel.blit(body, (int(18 * ui_scale), int(54 * ui_scale)))
        surface.blit(panel, (int(42 * ui_scale), surface.get_height() - panel_height - int(218 * ui_scale)))

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return
        self.scale = ui_scale
        self._text_cache.clear()
        self.eyebrow_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.title_font = pygame.font.SysFont("segoeui", max(16, int(18 * ui_scale)), bold=True)
        self.body_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))


class SkyContextStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.label_font: pygame.font.Font | None = None
        self.meta_font: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple[int, ...]], pygame.Surface] = {}

    def draw(
        self,
        surface: pygame.Surface,
        markers: list[tuple[str, float, tuple[int, int, int]]],
        ui_scale: float,
    ) -> None:
        if not markers:
            return

        self._ensure_fonts(ui_scale)
        panel_width = int(min(surface.get_width() * 0.34, 540 * ui_scale))
        panel_height = int(116 * ui_scale)
        x = surface.get_width() - panel_width - int(42 * ui_scale)
        y = surface.get_height() - panel_height - int(198 * ui_scale)
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 11, 18, 214), panel.get_rect(), border_radius=int(18 * ui_scale))
        pygame.draw.rect(panel, (46, 54, 68, 224), panel.get_rect(), width=1, border_radius=int(18 * ui_scale))

        title = render_cached(self._text_cache, self.label_font, "EARTH SKY CONTEXT", (128, 138, 156))
        meta = render_cached(self._text_cache, self.meta_font, "Approximate ecliptic longitudes as seen from Earth", (94, 104, 124))
        panel.blit(title, (int(18 * ui_scale), int(12 * ui_scale)))
        panel.blit(meta, (int(18 * ui_scale), int(30 * ui_scale)))

        track_left = int(24 * ui_scale)
        track_right = panel_width - int(24 * ui_scale)
        track_y = int(80 * ui_scale)
        pygame.draw.line(panel, (56, 66, 84), (track_left, track_y), (track_right, track_y), 2)

        zodiac = ("Ar", "Ta", "Ge", "Ca", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi")
        for index, label in enumerate(zodiac):
            tick_x = track_left + int((track_right - track_left) * index / 11)
            pygame.draw.line(panel, (48, 58, 72), (tick_x, track_y - 8), (tick_x, track_y + 8), 1)
            tag = render_cached(self._text_cache, self.meta_font, label, (100, 112, 134))
            panel.blit(tag, (tick_x - tag.get_width() // 2, track_y + int(12 * ui_scale)))

        for name, longitude_deg, color in markers:
            ratio = (longitude_deg % 360.0) / 360.0
            marker_x = track_left + int((track_right - track_left) * ratio)
            pygame.draw.circle(panel, (*color, 255), (marker_x, track_y), max(3, int(4 * ui_scale)))
            label = render_cached(self._text_cache, self.meta_font, name, (214, 220, 230))
            label_pos = Vector2(marker_x - label.get_width() / 2, track_y - int(26 * ui_scale))
            panel.blit(label, (int(label_pos.x), int(label_pos.y)))

        surface.blit(panel, (x, y))

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return
        self.scale = ui_scale
        self._text_cache.clear()
        self.label_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.meta_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)))
