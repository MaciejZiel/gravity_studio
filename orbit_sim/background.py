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
    parallax: float


class StarField:
    def __init__(self, size: tuple[int, int], seed: int = 42) -> None:
        self.size = size
        self.rng = Random(seed)
        self.base_surface = pygame.Surface(size)
        self.base_surface.fill((3, 5, 10))
        self.haze_surface = pygame.Surface(size, pygame.SRCALPHA)
        self.static_surface = pygame.Surface(size)
        self.twinkle_surface = pygame.Surface(size, pygame.SRCALPHA)
        self._static_cache_key: tuple[int, int] | None = None
        self._twinkle_cache_key: tuple[int, int, int] | None = None
        self.star_layers: list[tuple[float, pygame.Surface]] = []
        self.dynamic_stars: list[BackgroundStar] = []
        self._build_field()

    def draw(self, surface: pygame.Surface, elapsed_time: float, parallax: pygame.Vector2 | None = None) -> None:
        parallax = parallax or pygame.Vector2()
        static_key = (int(parallax.x), int(parallax.y))
        if static_key != self._static_cache_key:
            self._static_cache_key = static_key
            self.static_surface.blit(self.base_surface, (0, 0))
            self.static_surface.blit(self.haze_surface, self._offset_point(parallax * 0.08))
            for factor, layer in self.star_layers:
                self.static_surface.blit(layer, self._offset_point(parallax * factor))
        surface.blit(self.static_surface, (0, 0))
        twinkle_key = (int(elapsed_time * 8.0), int(parallax.x), int(parallax.y))
        if twinkle_key != self._twinkle_cache_key:
            self._twinkle_cache_key = twinkle_key
            self.twinkle_surface.fill((0, 0, 0, 0))
            for star in self.dynamic_stars:
                pulse = 0.78 + 0.22 * sin(elapsed_time * star.speed + star.phase)
                alpha = max(18, min(255, int(star.alpha * pulse)))
                x = int(star.x + parallax.x * star.parallax)
                y = int(star.y + parallax.y * star.parallax)
                pygame.draw.circle(self.twinkle_surface, (*star.color, alpha), (x, y), star.radius)

        surface.blit(self.twinkle_surface, (0, 0))

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
        centers = (
            ((int(width * 0.18), int(height * 0.26)), (int(width * 0.3), int(height * 0.18)), (30, 42, 68, 40)),
            ((int(width * 0.78), int(height * 0.7)), (int(width * 0.34), int(height * 0.22)), (18, 30, 52, 34)),
            ((int(width * 0.48), int(height * 0.52)), (int(width * 0.5), int(height * 0.14)), (28, 35, 52, 24)),
        )

        for center, radii, color in centers:
            rect = pygame.Rect(0, 0, radii[0], radii[1])
            rect.center = center
            pygame.draw.ellipse(self.haze_surface, color, rect)

        vignette = pygame.Surface(self.size, pygame.SRCALPHA)
        for radius_factor, alpha in ((0.62, 24), (0.78, 18), (0.92, 10)):
            rect = pygame.Rect(0, 0, int(width * radius_factor), int(height * radius_factor))
            rect.center = (width // 2, height // 2)
            pygame.draw.ellipse(vignette, (0, 0, 0, alpha), rect, width=max(1, int(min(width, height) * 0.04)))

        self.haze_surface.blit(vignette, (0, 0))

    def _draw_static_stars(self) -> None:
        width, height = self.size
        star_count = max(220, int(width * height / 9000))
        layer_specs = (0.04, 0.08, 0.14)
        layer_surfaces = [pygame.Surface(self.size, pygame.SRCALPHA) for _ in layer_specs]

        for index in range(star_count):
            radius = self.rng.choice((1, 1, 1, 1, 2))
            alpha = self.rng.randint(18, 120)
            color = self.rng.choice(((176, 186, 207), (205, 214, 229), (240, 237, 226)))
            parallax = self.rng.choice(layer_specs)
            star = BackgroundStar(
                x=self.rng.randint(0, width - 1),
                y=self.rng.randint(0, height - 1),
                radius=radius,
                alpha=alpha,
                phase=self.rng.uniform(0, 6.28),
                speed=self.rng.uniform(0.15, 0.55),
                color=color,
                parallax=parallax,
            )

            if index % 7 == 0 and alpha > 70:
                self.dynamic_stars.append(star)
            else:
                layer_index = layer_specs.index(parallax)
                pygame.draw.circle(layer_surfaces[layer_index], (*color, alpha), (star.x, star.y), radius)

        self.star_layers = list(zip(layer_specs, layer_surfaces))

    def _offset_point(self, parallax: pygame.Vector2) -> tuple[int, int]:
        return int(parallax.x), int(parallax.y)
