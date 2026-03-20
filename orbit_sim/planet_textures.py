from __future__ import annotations

from pathlib import Path

import pygame


ASSET_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "planets"


class PlanetTextureLibrary:
    def __init__(self) -> None:
        self._source_cache: dict[str, pygame.Surface | None] = {}
        self._square_cache: dict[tuple[str, int], pygame.Surface | None] = {}
        self._portrait_cache: dict[tuple[str, int], pygame.Surface | None] = {}

    def has_texture(self, body_name: str) -> bool:
        return self._path_for(body_name).exists()

    def square_texture(self, body_name: str, size: int) -> pygame.Surface | None:
        safe_size = max(64, int(size))
        cache_key = (body_name, safe_size)
        if cache_key not in self._square_cache:
            source = self._source(body_name)
            if source is None:
                self._square_cache[cache_key] = None
            else:
                square = self._center_square_crop(source)
                self._square_cache[cache_key] = pygame.transform.smoothscale(square, (safe_size, safe_size))
        return self._square_cache[cache_key]

    def portrait(self, body_name: str, diameter: int) -> pygame.Surface | None:
        safe_diameter = max(64, int(diameter))
        cache_key = (body_name, safe_diameter)
        if cache_key not in self._portrait_cache:
            square = self.square_texture(body_name, safe_diameter)
            self._portrait_cache[cache_key] = None if square is None else self._build_portrait(square, safe_diameter)
        return self._portrait_cache[cache_key]

    def clear_scaled_cache(self) -> None:
        self._square_cache.clear()
        self._portrait_cache.clear()

    def _source(self, body_name: str) -> pygame.Surface | None:
        if body_name not in self._source_cache:
            path = self._path_for(body_name)
            if not path.exists():
                self._source_cache[body_name] = None
            else:
                image = pygame.image.load(str(path))
                self._source_cache[body_name] = image.convert_alpha() if image.get_alpha() else image.convert()
        return self._source_cache[body_name]

    def _build_portrait(self, source: pygame.Surface, diameter: int) -> pygame.Surface:
        portrait = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        portrait.blit(source, (0, 0))

        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        radius = diameter // 2
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
        portrait.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return portrait

    def _center_square_crop(self, source: pygame.Surface) -> pygame.Surface:
        size = min(source.get_width(), source.get_height())
        crop_rect = pygame.Rect(0, 0, size, size)
        crop_rect.center = source.get_rect().center
        return source.subsurface(crop_rect).copy()

    def _path_for(self, body_name: str) -> Path:
        return ASSET_DIRECTORY / f"{body_name.lower()}.jpg"
