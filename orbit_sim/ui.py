from __future__ import annotations

import math

import pygame

from orbit_sim.models import CelestialBody


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

