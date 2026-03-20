from __future__ import annotations

from pathlib import Path

import pygame


ASSET_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "planets"


class PlanetTextureLibrary:
    def __init__(self) -> None:
        self._source_cache: dict[str, pygame.Surface | None] = {}
        self._map_cache: dict[tuple[str, int], pygame.Surface | None] = {}
        self._aux_cache: dict[str, pygame.Surface | None] = {}
        self._scaled_aux_cache: dict[tuple[str, int, int], pygame.Surface | None] = {}

    def has_texture(self, body_name: str) -> bool:
        return self._path_for(body_name).exists()

    def map_texture(self, body_name: str, width: int) -> pygame.Surface | None:
        safe_width = max(256, int(width))
        cache_key = (body_name, safe_width)
        if cache_key not in self._map_cache:
            source = self._source(body_name)
            if source is None:
                self._map_cache[cache_key] = None
            else:
                scaled_height = max(128, safe_width // 2)
                self._map_cache[cache_key] = pygame.transform.smoothscale(source, (safe_width, scaled_height))
        return self._map_cache[cache_key]

    def clear_scaled_cache(self) -> None:
        self._map_cache.clear()
        self._scaled_aux_cache.clear()

    def auxiliary_texture(self, key: str, size: tuple[int, int]) -> pygame.Surface | None:
        safe_width = max(128, int(size[0]))
        safe_height = max(32, int(size[1]))
        cache_key = (key, safe_width, safe_height)
        if cache_key not in self._scaled_aux_cache:
            source = self._aux_source(key)
            if source is None:
                self._scaled_aux_cache[cache_key] = None
            else:
                self._scaled_aux_cache[cache_key] = pygame.transform.smoothscale(source, (safe_width, safe_height))
        return self._scaled_aux_cache[cache_key]

    def _source(self, body_name: str) -> pygame.Surface | None:
        if body_name not in self._source_cache:
            path = self._path_for(body_name)
            if not path.exists():
                self._source_cache[body_name] = None
            else:
                image = pygame.image.load(str(path))
                self._source_cache[body_name] = image.convert_alpha() if image.get_alpha() else image.convert()
        return self._source_cache[body_name]

    def _aux_source(self, key: str) -> pygame.Surface | None:
        if key not in self._aux_cache:
            path = self._aux_path_for(key)
            if not path.exists():
                self._aux_cache[key] = None
            else:
                image = pygame.image.load(str(path))
                self._aux_cache[key] = image.convert_alpha() if image.get_alpha() else image.convert()
        return self._aux_cache[key]

    def _path_for(self, body_name: str) -> Path:
        return ASSET_DIRECTORY / f"{body_name.lower()}.jpg"

    def _aux_path_for(self, key: str) -> Path:
        for extension in (".png", ".jpg"):
            candidate = ASSET_DIRECTORY / f"{key}{extension}"
            if candidate.exists():
                return candidate
        return ASSET_DIRECTORY / f"{key}.png"
