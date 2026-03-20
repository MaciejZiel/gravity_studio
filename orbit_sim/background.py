from __future__ import annotations

from dataclasses import dataclass
from math import sin
from random import Random

import pygame


@dataclass
class BackgroundStar:
    x: int
    y: int
    radius: int
    alpha: int
    phase: float
    speed: float
    color: tuple[int, int, int]


class StarField:
    def __init__(self, size: tuple[int, int], seed: int = 42) -> None:
        rng = Random(seed)
        width, height = size
        self.stars = [
            BackgroundStar(
                x=rng.randint(0, width),
                y=rng.randint(0, height),
                radius=rng.choice((1, 1, 1, 2)),
                alpha=rng.randint(28, 120),
                phase=rng.uniform(0, 6.28),
                speed=rng.uniform(0.25, 0.85),
                color=rng.choice(((144, 168, 216), (169, 188, 232), (241, 235, 221))),
            )
            for _ in range(180)
        ]

    def draw(self, surface: pygame.Surface, elapsed_time: float) -> None:
        stars_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for star in self.stars:
            pulse = 0.65 + 0.35 * sin(elapsed_time * star.speed + star.phase)
            alpha = max(18, min(255, int(star.alpha * pulse)))
            pygame.draw.circle(stars_surface, (*star.color, alpha), (star.x, star.y), star.radius)

        surface.blit(stars_surface, (0, 0))

