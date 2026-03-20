from __future__ import annotations

from dataclasses import dataclass

import pygame

from orbit_sim.models import CelestialBody


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


class InfoPanel:
    def __init__(self) -> None:
        self.scale = 0.0
        self.eyebrow_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.label_font: pygame.font.Font | None = None
        self.value_font: pygame.font.Font | None = None
        self.fact_font: pygame.font.Font | None = None

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
        eyebrow = self.eyebrow_font.render("SELECTED PLANET", True, (150, 160, 178))
        title = self.title_font.render(body.name, True, (234, 238, 244))
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

        comparison_title = self.label_font.render("Compared with Earth", True, (132, 142, 160))
        comparison_value = self.fact_font.render(self._comparison_text(body), True, (208, 214, 224))
        panel.blit(comparison_title, (int(24 * ui_scale), int(248 * ui_scale)))
        panel.blit(comparison_value, (int(24 * ui_scale), int(268 * ui_scale)))

        fact_title = self.label_font.render("Fact", True, (132, 142, 160))
        panel.blit(fact_title, (int(24 * ui_scale), int(298 * ui_scale)))
        fact_lines = self._wrap_text(body.fact, self.fact_font, panel_width - int(48 * ui_scale))
        text_y = int(318 * ui_scale)
        for line in fact_lines[:2]:
            line_surface = self.fact_font.render(line, True, (208, 214, 224))
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
        label_surface = self.label_font.render(label, True, (132, 142, 160))
        value_surface = self.value_font.render(value, True, (226, 231, 238))
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
        title = self.title_font.render("SOLAR SYSTEM", True, (230, 235, 242))
        subtitle = self.subtitle_font.render("Astronomy-inspired orbital visualization", True, (124, 136, 156))
        status_label = "PAUSED" if paused else ("REAL-TIME" if live_mode else "SIMULATING")
        meta = self.meta_font.render(
            f"{status_label}   |   {scene_label.upper()}   |   {time_speed_label}   |   ZOOM {int(zoom * 100)}%   |   SCALE {scale_mode.upper()}",
            True,
            (106, 118, 140),
        )
        hint = self.meta_font.render("Q/W/E scenes, 1-4 time, H hide UI, P capture, click to focus.", True, (88, 100, 120))

        surface.blit(title, (margin_x, int(34 * ui_scale)))
        surface.blit(subtitle, (margin_x, int(70 * ui_scale)))
        surface.blit(meta, (margin_x, int(102 * ui_scale)))
        surface.blit(hint, (margin_x, int(124 * ui_scale)))
        self._draw_clock_badge(surface, local_time_label, timezone_label, ui_scale)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self.title_font = pygame.font.SysFont("segoeui", max(20, int(28 * ui_scale)), bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", max(13, int(15 * ui_scale)))
        self.meta_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
        self.note_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)), bold=True)
        self.clock_font = pygame.font.SysFont("segoeui", max(16, int(20 * ui_scale)), bold=True)

    def draw_notification(self, surface: pygame.Surface, text: str, timer: float, ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        alpha = max(0, min(255, int(255 * min(1.0, timer))))
        label_surface = self.note_font.render(text, True, (230, 235, 242))
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

        label = self.meta_font.render("LOCAL CLOCK", True, (124, 136, 156))
        value = self.clock_font.render(local_time_label, True, (232, 236, 241))
        timezone = self.meta_font.render(timezone_label, True, (110, 120, 138))
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

    def draw(
        self,
        surface: pygame.Surface,
        body: CelestialBody,
        local_time_label: str,
        simulation_time_label: str,
        ui_scale: float,
    ) -> None:
        self._ensure_fonts(ui_scale)
        panel_width = int(272 * ui_scale)
        panel_height = int(148 * ui_scale)
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 19, 224), panel.get_rect(), border_radius=int(22 * ui_scale))
        pygame.draw.rect(panel, (50, 58, 72, 228), panel.get_rect(), width=1, border_radius=int(22 * ui_scale))

        eyebrow = self.eyebrow_font.render("LIVE CLOSE-UP", True, (138, 148, 166))
        title = self.title_font.render(body.name, True, (232, 236, 242))
        panel.blit(eyebrow, (int(20 * ui_scale), int(18 * ui_scale)))
        panel.blit(title, (int(20 * ui_scale), int(38 * ui_scale)))

        self._draw_time_row(panel, "Local", local_time_label, int(74 * ui_scale), ui_scale)
        self._draw_time_row(panel, "Sim", simulation_time_label, int(98 * ui_scale), ui_scale)
        hint = self.meta_font.render("Drag sphere to rotate", True, (112, 124, 144))
        panel.blit(hint, (int(20 * ui_scale), int(124 * ui_scale)))

        x = int(42 * ui_scale)
        y = int(surface.get_height() * 0.71)
        surface.blit(panel, (x, y))

    def _draw_time_row(self, panel: pygame.Surface, label: str, value: str, top: int, ui_scale: float) -> None:
        label_surface = self.label_font.render(label, True, (128, 138, 156))
        value_surface = self.value_font.render(value, True, (222, 228, 236))
        panel.blit(label_surface, (int(20 * ui_scale), top))
        panel.blit(value_surface, (panel.get_width() - value_surface.get_width() - int(20 * ui_scale), top - int(1 * ui_scale)))

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self.eyebrow_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.title_font = pygame.font.SysFont("segoeui", max(20, int(24 * ui_scale)), bold=True)
        self.label_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
        self.value_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)))
        self.meta_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)))


class ControlBar:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None

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
            label_surface = self.button_font.render(button.label, True, text_color)
            label_rect = label_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label_surface, label_rect)
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self.button_font = pygame.font.SysFont("segoeui", max(12, int(14 * ui_scale)), bold=True)


class SceneStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None

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
            label_surface = self.button_font.render(button.label, True, (224, 229, 237))
            label_rect = label_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label_surface, label_rect)
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self.button_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)), bold=True)


class DateShortcutStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.button_font: pygame.font.Font | None = None
        self.label_font: pygame.font.Font | None = None

    def build_buttons(self, width: int, height: int, ui_scale: float, active_action: str | None) -> list[ControlButton]:
        self._ensure_fonts(ui_scale)
        labels = [
            ("jump_now", "Now"),
            ("jump_equinox", "Equinox"),
            ("jump_solstice", "Solstice"),
            ("jump_apollo", "Apollo 11"),
            ("jump_voyager", "Voyager 1"),
        ]
        y = height - int(170 * ui_scale)
        x = int(width * 0.5) - int(340 * ui_scale)
        gap = int(8 * ui_scale)
        buttons: list[ControlButton] = []
        for action, label in labels:
            button_width = max(int(70 * ui_scale), self.button_font.size(label)[0] + int(24 * ui_scale))
            rect = pygame.Rect(x, y, button_width, int(28 * ui_scale))
            buttons.append(ControlButton(action=action, label=label, rect=rect, active=action == active_action))
            x += button_width + gap
        return buttons

    def draw(self, surface: pygame.Surface, buttons: list[ControlButton], ui_scale: float) -> None:
        self._ensure_fonts(ui_scale)
        if not buttons:
            return

        label = self.label_font.render("QUICK DATES", True, (118, 128, 146))
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
            text = self.button_font.render(button.label, True, (220, 226, 234))
            chip.blit(text, text.get_rect(center=chip.get_rect().center))
            surface.blit(chip, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self.button_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.label_font = pygame.font.SysFont("segoeui", max(9, int(10 * ui_scale)), bold=True)


class TimelineStrip:
    def __init__(self) -> None:
        self.scale = 0.0
        self.label_font: pygame.font.Font | None = None
        self.meta_font: pygame.font.Font | None = None
        self.speed_font: pygame.font.Font | None = None

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

        label_surface = self.label_font.render("SIMULATION TIME", True, (126, 136, 154))
        value_surface = self.meta_font.render(date_label, True, (228, 233, 240))
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
            label = self.speed_font.render(button.label, True, (220, 226, 234))
            label_rect = label.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label, label_rect)
            surface.blit(button_surface, button.rect.topleft)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.scale) < 0.01:
            return

        self.scale = ui_scale
        self.label_font = pygame.font.SysFont("segoeui", max(10, int(11 * ui_scale)), bold=True)
        self.meta_font = pygame.font.SysFont("segoeui", max(13, int(15 * ui_scale)))
        self.speed_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)), bold=True)
