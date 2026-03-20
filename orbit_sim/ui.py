from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from orbit_sim.models import CelestialBody


@dataclass
class ControlButton:
    action: str
    label: str
    rect: pygame.Rect
    active: bool = False


class InfoPanel:
    def __init__(self) -> None:
        self.eyebrow_font = pygame.font.SysFont("segoeui", 12, bold=True)
        self.title_font = pygame.font.SysFont("segoeui", 28, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", 13)
        self.value_font = pygame.font.SysFont("segoeui", 18)

    def draw(self, surface: pygame.Surface, body: CelestialBody, visibility: float) -> None:
        panel_width = 284
        panel_height = 236
        slide = int((1.0 - visibility) * 24)
        alpha = max(0, min(255, int(visibility * 255)))
        x = surface.get_width() - panel_width - 34 + slide
        y = 32

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        shadow = pygame.Surface((panel_width + 20, panel_height + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, int(alpha * 0.32)), shadow.get_rect(), border_radius=30)
        surface.blit(shadow, (x - 10 + slide, y + 8))

        pygame.draw.rect(panel, (10, 15, 28, int(alpha * 0.94)), panel.get_rect(), border_radius=24)
        pygame.draw.rect(panel, (56, 74, 108, int(alpha * 0.78)), panel.get_rect(), width=1, border_radius=24)
        pygame.draw.circle(panel, (*body.color, int(alpha * 0.95)), (34, 36), 8)

        eyebrow = self.eyebrow_font.render("SELECTED BODY", True, (154, 167, 196))
        title = self.title_font.render(body.name, True, (236, 240, 248))

        panel.blit(eyebrow, (54, 26))
        panel.blit(title, (26, 56))
        self._draw_stat_row(panel, "Orbit radius", f"{body.orbit_radius:.0f} px", 116, alpha)
        self._draw_stat_row(panel, "Speed", f"{math.degrees(body.angular_speed):.1f} deg/s", 154, alpha)
        self._draw_stat_row(panel, "Size", f"{body.radius:.0f} px", 192, alpha)

        surface.blit(panel, (x, y))

    def _draw_stat_row(self, panel: pygame.Surface, label: str, value: str, top: int, alpha: int) -> None:
        pygame.draw.line(panel, (42, 54, 82, int(alpha * 0.8)), (26, top - 10), (258, top - 10), 1)
        label_surface = self.label_font.render(label, True, (119, 132, 160))
        value_surface = self.value_font.render(value, True, (228, 233, 244))
        panel.blit(label_surface, (26, top))
        panel.blit(value_surface, (168, top - 2))


class ControlBar:
    def __init__(self) -> None:
        self.button_font = pygame.font.SysFont("segoeui", 16, bold=True)

    def build_buttons(self, width: int, height: int, paused: bool) -> list[ControlButton]:
        labels = [
            ("add_planet", "Add Planet", False),
            ("toggle_pause", "Resume" if paused else "Pause", paused),
            ("reset", "Reset", False),
        ]
        buttons: list[ControlButton] = []
        x = 34
        y = height - 82

        for action, label, active in labels:
            button_width = max(104, self.button_font.size(label)[0] + 34)
            rect = pygame.Rect(x, y, button_width, 46)
            buttons.append(ControlButton(action=action, label=label, rect=rect, active=active))
            x += button_width + 12

        return buttons

    def draw(self, surface: pygame.Surface, buttons: list[ControlButton], hovered_action: str | None) -> None:
        if not buttons:
            return

        bar_rect = buttons[0].rect.unionall([button.rect for button in buttons[1:]]).inflate(22, 20)
        shadow = pygame.Surface((bar_rect.width + 20, bar_rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 76), shadow.get_rect(), border_radius=28)
        surface.blit(shadow, (bar_rect.x - 10, bar_rect.y + 8))

        bar = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bar, (9, 13, 24, 230), bar.get_rect(), border_radius=24)
        pygame.draw.rect(bar, (47, 61, 92, 196), bar.get_rect(), width=1, border_radius=24)
        surface.blit(bar, bar_rect.topleft)

        for button in buttons:
            state_fill = (15, 20, 36, 255)
            state_border = (55, 72, 108, 255)
            text_color = (222, 229, 242)

            if button.active:
                state_fill = (31, 57, 72, 255)
                state_border = (79, 155, 189, 255)
            elif button.action == hovered_action:
                state_fill = (21, 28, 49, 255)
                state_border = (88, 110, 160, 255)

            button_surface = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(button_surface, state_fill, button_surface.get_rect(), border_radius=18)
            pygame.draw.rect(button_surface, state_border, button_surface.get_rect(), width=1, border_radius=18)

            label_surface = self.button_font.render(button.label, True, text_color)
            label_rect = label_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(label_surface, label_rect)
            surface.blit(button_surface, button.rect.topleft)
