from __future__ import annotations

import sys

import pygame


WINDOW_SIZE = (1440, 900)
BACKGROUND = (6, 10, 18)


class GravityStudioApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gravity Studio")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000
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
        _ = dt

    def render(self) -> None:
        self.screen.fill(BACKGROUND)
        pygame.display.flip()
