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
        self.size = size
        self.rng = Random(seed)
        self.base_surface = pygame.Surface(size)
        self.base_surface.fill((3, 5, 10))
        self.dynamic_stars: list[BackgroundStar] = []
        self._build_field()

    def draw(self, surface: pygame.Surface, elapsed_time: float) -> None:
        surface.blit(self.base_surface, (0, 0))
        twinkle_surface = pygame.Surface(self.size, pygame.SRCALPHA)

        for star in self.dynamic_stars:
            pulse = 0.78 + 0.22 * sin(elapsed_time * star.speed + star.phase)
            alpha = max(18, min(255, int(star.alpha * pulse)))
            pygame.draw.circle(twinkle_surface, (*star.color, alpha), (star.x, star.y), star.radius)

        surface.blit(twinkle_surface, (0, 0))

    def _build_field(self) -> None:
        width, height = self.size
        gradient = pygame.Surface(self.size, pygame.SRCALPHA)

        for y in range(height):
            t = y / max(1, height - 1)
            color = (
                int(3 + 5 * (1.0 - t)),
                int(6 + 7 * (1.0 - t)),
                int(12 + 12 * (1.0 - t)),
                255,
            )
            pygame.draw.line(gradient, color, (0, y), (width, y))

        self.base_surface.blit(gradient, (0, 0))
        self._draw_galactic_haze()
        self._draw_static_stars()

    def _draw_galactic_haze(self) -> None:
        width, height = self.size
        haze = pygame.Surface(self.size, pygame.SRCALPHA)
        centers = (
            ((int(width * 0.18), int(height * 0.26)), (int(width * 0.3), int(height * 0.18)), (30, 42, 68, 40)),
            ((int(width * 0.78), int(height * 0.7)), (int(width * 0.34), int(height * 0.22)), (18, 30, 52, 34)),
            ((int(width * 0.48), int(height * 0.52)), (int(width * 0.5), int(height * 0.14)), (28, 35, 52, 24)),
        )

        for center, radii, color in centers:
            rect = pygame.Rect(0, 0, radii[0], radii[1])
            rect.center = center
            pygame.draw.ellipse(haze, color, rect)

        vignette = pygame.Surface(self.size, pygame.SRCALPHA)
        for radius_factor, alpha in ((0.62, 24), (0.78, 18), (0.92, 10)):
            rect = pygame.Rect(0, 0, int(width * radius_factor), int(height * radius_factor))
            rect.center = (width // 2, height // 2)
            pygame.draw.ellipse(vignette, (0, 0, 0, alpha), rect, width=max(1, int(min(width, height) * 0.04)))

        self.base_surface.blit(haze, (0, 0))
        self.base_surface.blit(vignette, (0, 0))

    def _draw_static_stars(self) -> None:
        width, height = self.size
        star_count = max(220, int(width * height / 9000))
        static_surface = pygame.Surface(self.size, pygame.SRCALPHA)

        for index in range(star_count):
            radius = self.rng.choice((1, 1, 1, 1, 2))
            alpha = self.rng.randint(18, 120)
            color = self.rng.choice(((176, 186, 207), (205, 214, 229), (240, 237, 226)))
            star = BackgroundStar(
                x=self.rng.randint(0, width - 1),
                y=self.rng.randint(0, height - 1),
                radius=radius,
                alpha=alpha,
                phase=self.rng.uniform(0, 6.28),
                speed=self.rng.uniform(0.15, 0.55),
                color=color,
            )

            if index % 7 == 0 and alpha > 70:
                self.dynamic_stars.append(star)
            else:
                pygame.draw.circle(static_surface, (*color, alpha), (star.x, star.y), radius)

        self.base_surface.blit(static_surface, (0, 0))
