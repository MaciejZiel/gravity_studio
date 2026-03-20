from __future__ import annotations

import sys

import pygame

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
from orbit_sim.simulation import OrbitalSimulation


class GravityStudioApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gravity Studio")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("segoeui", 24)
        self.caption_font = pygame.font.SysFont("segoeui", 14)
        self.simulation = OrbitalSimulation()
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

    def update(self, dt: float) -> None:
        self.simulation.update(dt)

    def render(self) -> None:
        self.screen.fill(SPACE_COLOR)
        self.draw_space_haze()
        self.draw_star()
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

    def draw_heading(self) -> None:
        title = self.title_font.render("GRAVITY STUDIO", True, TITLE_TEXT)
        subtitle = self.caption_font.render("Orbital motion study", True, SUBTITLE_TEXT)
        self.screen.blit(title, (44, 34))
        self.screen.blit(subtitle, (46, 66))
