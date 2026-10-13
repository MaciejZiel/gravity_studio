from __future__ import annotations

from math import sin, tau

import pygame
from pygame import Vector2

_SPLASH_CACHE: dict[tuple[tuple[int, int], float], dict[str, object]] = {}


def create_window_icon(size: int = 96) -> pygame.Surface:
    icon = pygame.Surface((size, size), pygame.SRCALPHA)
    center = Vector2(size / 2, size / 2)
    pygame.draw.circle(icon, (10, 14, 22, 255), (int(center.x), int(center.y)), int(size * 0.48))
    pygame.draw.circle(icon, (242, 201, 124, 255), (int(center.x - size * 0.16), int(center.y - size * 0.18)), int(size * 0.11))
    pygame.draw.circle(icon, (88, 128, 208, 255), (int(center.x + size * 0.1), int(center.y + size * 0.05)), int(size * 0.17))
    ring_rect = pygame.Rect(0, 0, int(size * 0.56), int(size * 0.2))
    ring_rect.center = (int(center.x + size * 0.1), int(center.y + size * 0.05))
    pygame.draw.ellipse(icon, (214, 223, 238, 214), ring_rect, max(1, size // 24))
    pygame.draw.circle(icon, (214, 223, 238, 90), (int(center.x), int(center.y)), int(size * 0.46), max(1, size // 36))
    return icon


def draw_launch_splash(surface: pygame.Surface, elapsed_time: float, ui_scale: float) -> None:
    if elapsed_time >= 2.8:
        return

    progress = min(1.0, elapsed_time / 2.4)
    fade = 1.0 - min(1.0, max(0.0, (elapsed_time - 1.8) / 1.0))
    assets = _splash_assets(surface.get_size(), ui_scale)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((4, 6, 12, int(228 * fade)))
    overlay.blit(assets["title"], assets["title_rect"])
    overlay.blit(assets["subtitle"], assets["subtitle_rect"])
    overlay.blit(assets["meta"], assets["meta_rect"])

    emblem = assets["emblem"].copy()
    emblem_center = Vector2(emblem.get_width() / 2, emblem.get_height() / 2)
    for index, orbit_rect in enumerate(assets["orbit_rects"]):
        wobble = sin(elapsed_time * 0.7 + index) * 0.02
        pygame.draw.ellipse(emblem, (180, 192, 214, int((42 - index * 8) * fade)), orbit_rect, max(1, int((2 + index) * ui_scale)))
        angle = tau * (progress * 0.22 + 0.12 * index + wobble)
        point = emblem_center + Vector2(orbit_rect.width * 0.36 * sin(angle), orbit_rect.height * 0.43 * sin(angle + 1.2))
        pygame.draw.circle(emblem, (226, 232, 240, int(176 * fade)), (int(point.x), int(point.y)), max(2, int(4 * ui_scale)))

    overlay.blit(emblem, assets["emblem_rect"])

    track_rect = assets["track_rect"].copy()
    pygame.draw.rect(overlay, (26, 32, 46, int(220 * fade)), track_rect, border_radius=track_rect.height // 2)
    filled_rect = track_rect.copy()
    filled_rect.width = max(6, int(track_rect.width * progress))
    pygame.draw.rect(overlay, (124, 144, 184, int(240 * fade)), filled_rect, border_radius=track_rect.height // 2)

    surface.blit(overlay, (0, 0))


def _splash_assets(surface_size: tuple[int, int], ui_scale: float) -> dict[str, object]:
    cache_key = (surface_size, round(ui_scale, 2))
    if cache_key in _SPLASH_CACHE:
        return _SPLASH_CACHE[cache_key]

    center = Vector2(surface_size[0] / 2, surface_size[1] / 2)
    emblem_radius = int(84 * ui_scale)
    emblem = pygame.Surface((emblem_radius * 4, emblem_radius * 4), pygame.SRCALPHA)
    emblem_center = Vector2(emblem.get_width() / 2, emblem.get_height() / 2)
    pygame.draw.circle(emblem, (10, 14, 24, 190), (int(emblem_center.x), int(emblem_center.y)), int(emblem_radius * 1.46))
    pygame.draw.circle(emblem, (242, 204, 132, 255), (int(emblem_center.x - emblem_radius * 0.42), int(emblem_center.y - emblem_radius * 0.44)), int(emblem_radius * 0.24))
    pygame.draw.circle(emblem, (90, 128, 214, 255), (int(emblem_center.x + emblem_radius * 0.22), int(emblem_center.y + emblem_radius * 0.12)), int(emblem_radius * 0.38))

    title_font = pygame.font.SysFont("segoeui", max(30, int(42 * ui_scale)), bold=True)
    subtitle_font = pygame.font.SysFont("segoeui", max(14, int(16 * ui_scale)))
    meta_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
    title = title_font.render("GRAVITY STUDIO", True, (236, 240, 246))
    subtitle = subtitle_font.render("Solar System Explorer", True, (144, 154, 174))
    meta = meta_font.render("Preparing orbital layers, atmospheric shading and live ephemeris.", True, (110, 120, 140))

    orbit_rects = []
    for index in range(3):
        orbit_rect = pygame.Rect(0, 0, int(emblem_radius * (2.4 + index * 0.36)), int(emblem_radius * (0.78 + index * 0.14)))
        orbit_rect.center = (int(emblem_center.x), int(emblem_center.y))
        orbit_rects.append(orbit_rect)

    track_rect = pygame.Rect(0, 0, int(320 * ui_scale), int(8 * ui_scale))
    track_rect.center = (int(center.x), int(center.y + 166 * ui_scale))
    assets = {
        "emblem": emblem,
        "emblem_rect": emblem.get_rect(center=(int(center.x), int(center.y - 48 * ui_scale))),
        "orbit_rects": tuple(orbit_rects),
        "title": title,
        "title_rect": title.get_rect(center=(int(center.x), int(center.y + 74 * ui_scale))),
        "subtitle": subtitle,
        "subtitle_rect": subtitle.get_rect(center=(int(center.x), int(center.y + 106 * ui_scale))),
        "meta": meta,
        "meta_rect": meta.get_rect(center=(int(center.x), int(center.y + 130 * ui_scale))),
        "track_rect": track_rect,
    }
    _SPLASH_CACHE[cache_key] = assets
    if len(_SPLASH_CACHE) > 8:
        _SPLASH_CACHE.clear()
        _SPLASH_CACHE[cache_key] = assets
    return assets
