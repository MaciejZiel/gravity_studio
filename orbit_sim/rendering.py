from __future__ import annotations

from math import cos, sin, tau

import pygame
from pygame import Vector2

from orbit_sim.camera import SolarCamera
from orbit_sim.config import SPACE_HAZE, STAR_CORE, STAR_GLOW
from orbit_sim.models import CelestialBody


class SceneRenderer:
    def __init__(self) -> None:
        self.label_scale = 0.0
        self.label_font: pygame.font.Font | None = None
        self.selected_label_font: pygame.font.Font | None = None

    def draw(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        elapsed_time: float,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
        show_orbits: bool,
        show_labels: bool,
    ) -> None:
        self._ensure_fonts(camera.layout.ui_scale)
        self.draw_space_haze(surface, camera.zoom)
        if show_orbits:
            self.draw_orbits(surface, camera, bodies, selected_body)
        self.draw_star(surface, camera, elapsed_time)
        self.draw_planets(surface, camera, bodies, elapsed_time, hovered_body, selected_body)
        if show_labels:
            self.draw_labels(surface, camera, bodies, selected_body)

    def draw_space_haze(self, surface: pygame.Surface, zoom: float) -> None:
        size = surface.get_size()
        haze = pygame.Surface(size, pygame.SRCALPHA)
        center = (int(size[0] * 0.44), int(size[1] * 0.54))
        haze_scale = 0.9 + (zoom - 1.0) * 0.18

        min_dimension = min(size)
        for radius_factor, alpha in ((0.5, 9), (0.32, 18), (0.2, 28)):
            radius = int(min_dimension * radius_factor)
            pygame.draw.circle(haze, (*SPACE_HAZE, alpha), center, int(radius * haze_scale))

        surface.blit(haze, (0, 0))

    def draw_star(self, surface: pygame.Surface, camera: SolarCamera, elapsed_time: float) -> None:
        center_vector = camera.layout.scene_center
        center = (int(center_vector.x), int(center_vector.y))
        pulse = 1.0 + sin(elapsed_time * 0.9) * 0.018
        base_glow = int(camera.sun_radius() * 14)
        star_scale = pulse
        glow_size = int(base_glow * star_scale)
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_center = (glow_size // 2, glow_size // 2)
        glow_center_vector = Vector2(glow_center)

        for radius_factor, alpha in ((0.42, 5), (0.28, 10), (0.18, 18), (0.11, 34)):
            pygame.draw.circle(glow, (*STAR_GLOW, alpha), glow_center, max(1, int(glow_size * radius_factor)))
        self._draw_solar_corona(glow, glow_center_vector, glow_size, elapsed_time)

        surface.blit(
            glow,
            (center[0] - glow_size // 2, center[1] - glow_size // 2),
            special_flags=pygame.BLEND_ALPHA_SDL2,
        )
        sun_outer = max(16, int(camera.sun_radius() * star_scale))
        sun_inner = max(10, int(sun_outer * 0.62))
        solar_disc = pygame.Surface((sun_outer * 5, sun_outer * 5), pygame.SRCALPHA)
        disc_center = Vector2(solar_disc.get_width() / 2, solar_disc.get_height() / 2)
        self._draw_solar_disc(solar_disc, disc_center, sun_outer, elapsed_time)
        surface.blit(solar_disc, (center[0] - solar_disc.get_width() // 2, center[1] - solar_disc.get_height() // 2), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(surface, STAR_CORE, center, sun_inner)

    def draw_orbits(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        selected_body: CelestialBody | None,
    ) -> None:
        orbit_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        center = (int(camera.layout.scene_center.x), int(camera.layout.scene_center.y))

        for body in bodies:
            scaled_radius = int(camera.orbit_radius(body))
            base_color = (112, 121, 138, 24)
            if body is selected_body:
                base_color = (194, 203, 214, 52)

            pygame.draw.circle(orbit_surface, base_color, center, scaled_radius, 1)

        surface.blit(orbit_surface, (0, 0))

    def draw_planets(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        elapsed_time: float,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
    ) -> None:
        for body in bodies:
            position = camera.body_position(body)
            screen_pos = (int(position.x), int(position.y))
            planet_radius = max(3, int(camera.planet_radius(body)))
            is_hovered = body is hovered_body
            is_selected = body is selected_body
            light_vector = (camera.layout.scene_center - position)
            if light_vector.length_squared() > 0:
                light_vector = light_vector.normalize()
            else:
                light_vector = Vector2(-1, -1).normalize()

            self._draw_planet_halo(surface, screen_pos, planet_radius, body)
            if body.has_rings:
                self._draw_saturn_rings(surface, screen_pos, planet_radius, front=False)

            if is_hovered or is_selected:
                ring_color = (216, 222, 231) if is_selected else (162, 169, 179)
                ring_radius = planet_radius + (7 if is_selected else 5)
                pygame.draw.circle(surface, ring_color, screen_pos, ring_radius, 1)

            planet_surface = pygame.Surface((planet_radius * 4, planet_radius * 4), pygame.SRCALPHA)
            local_center = Vector2(planet_radius * 2, planet_radius * 2)
            self._draw_planet_sprite(planet_surface, local_center, planet_radius, body, light_vector)
            surface.blit(
                planet_surface,
                (screen_pos[0] - planet_radius * 2, screen_pos[1] - planet_radius * 2),
            )
            if body.has_rings:
                self._draw_saturn_rings(surface, screen_pos, planet_radius, front=True)

    def _draw_planet_sprite(
        self,
        surface: pygame.Surface,
        center: Vector2,
        radius: int,
        body: CelestialBody,
        light_vector: Vector2,
    ) -> None:
        base_color = body.color
        shadow_color = self._darken(body.color, 0.48)
        rim_color = body.accent_color

        pygame.draw.circle(surface, base_color, self._point(center), radius)
        self._draw_surface_features(surface, center, radius, body)

        shadow_offset = center - light_vector * radius * 0.28
        shadow_radius = int(radius * 1.02)
        pygame.draw.circle(surface, (*shadow_color, 156), self._point(shadow_offset), shadow_radius)
        pygame.draw.circle(surface, base_color, self._point(center + light_vector * radius * 0.08), int(radius * 0.92))
        self._draw_surface_features(surface, center + light_vector * radius * 0.08, int(radius * 0.92), body)
        pygame.draw.circle(
            surface,
            (*self._darken(body.color, 0.66), 96),
            self._point(center - light_vector * radius * 0.34),
            int(radius * 0.62),
        )

        highlight_center = center + light_vector * radius * 0.34
        pygame.draw.circle(surface, (*rim_color, 108), self._point(highlight_center), max(2, int(radius * 0.36)))
        pygame.draw.circle(
            surface,
            (255, 255, 255, 48),
            self._point(center + light_vector * radius * 0.5),
            max(2, radius // 6),
        )
        pygame.draw.circle(surface, (*rim_color, 52), self._point(center), radius, 1)
        self._draw_atmosphere(surface, center, radius, body, light_vector)

    def _draw_surface_features(
        self,
        surface: pygame.Surface,
        center: Vector2,
        radius: int,
        body: CelestialBody,
    ) -> None:
        rect = pygame.Rect(int(center.x - radius), int(center.y - radius), radius * 2, radius * 2)

        if body.name in {"Jupiter", "Saturn", "Uranus", "Neptune"}:
            self._draw_gas_bands(surface, rect, body)
        else:
            self._draw_terrestrial_markings(surface, center, radius, body)

    def _draw_gas_bands(self, surface: pygame.Surface, rect: pygame.Rect, body: CelestialBody) -> None:
        band_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        center_y = rect.height // 2
        band_specs = {
            "Jupiter": ((0.52, 0.18), (0.40, 0.11), (0.63, 0.08)),
            "Saturn": ((0.54, 0.12), (0.42, 0.08), (0.67, 0.05)),
            "Uranus": ((0.50, 0.06), (0.36, 0.04)),
            "Neptune": ((0.50, 0.08), (0.36, 0.05)),
        }

        for y_factor, strength in band_specs.get(body.name, ()):
            y = int(rect.height * y_factor)
            height = max(2, int(rect.height * 0.13))
            color = (*self._lighten(body.color, 1.0 + strength), 52)
            band_rect = pygame.Rect(int(rect.width * 0.1), y - height // 2, int(rect.width * 0.8), height)
            pygame.draw.ellipse(band_surface, color, band_rect)

        if body.name == "Jupiter":
            spot_rect = pygame.Rect(0, 0, int(rect.width * 0.22), int(rect.height * 0.14))
            spot_rect.center = (int(rect.width * 0.62), int(rect.height * 0.57))
            pygame.draw.ellipse(band_surface, (188, 122, 92, 98), spot_rect)
        elif body.name == "Neptune":
            storm_rect = pygame.Rect(0, 0, int(rect.width * 0.18), int(rect.height * 0.12))
            storm_rect.center = (int(rect.width * 0.42), int(rect.height * 0.46))
            pygame.draw.ellipse(band_surface, (168, 196, 236, 54), storm_rect)

        surface.blit(band_surface, rect.topleft, special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_terrestrial_markings(
        self,
        surface: pygame.Surface,
        center: Vector2,
        radius: int,
        body: CelestialBody,
    ) -> None:
        if body.name == "Earth":
            pygame.draw.circle(surface, (114, 143, 96, 110), self._point(center + Vector2(-radius * 0.18, -radius * 0.05)), max(2, int(radius * 0.26)))
            pygame.draw.circle(surface, (123, 152, 102, 90), self._point(center + Vector2(radius * 0.1, radius * 0.22)), max(2, int(radius * 0.2)))
            pygame.draw.circle(surface, (232, 239, 245, 68), self._point(center + Vector2(radius * 0.04, -radius * 0.22)), max(2, int(radius * 0.18)))
            pygame.draw.circle(surface, (232, 239, 245, 44), self._point(center + Vector2(-radius * 0.24, radius * 0.18)), max(2, int(radius * 0.13)))
        elif body.name == "Mars":
            pygame.draw.circle(surface, (188, 146, 124, 70), self._point(center + Vector2(radius * 0.12, -radius * 0.2)), max(2, int(radius * 0.18)))
            pygame.draw.circle(surface, (120, 82, 64, 74), self._point(center + Vector2(-radius * 0.24, radius * 0.14)), max(2, int(radius * 0.22)))
            pygame.draw.circle(surface, (240, 236, 230, 76), self._point(center + Vector2(0, -radius * 0.56)), max(2, int(radius * 0.12)))
        elif body.name == "Venus":
            pygame.draw.circle(surface, (204, 184, 148, 58), self._point(center + Vector2(-radius * 0.16, 0)), max(2, int(radius * 0.34)))
            pygame.draw.circle(surface, (232, 220, 190, 42), self._point(center + Vector2(radius * 0.18, -radius * 0.22)), max(2, int(radius * 0.22)))
        elif body.name == "Mercury":
            pygame.draw.circle(surface, (176, 168, 156, 54), self._point(center + Vector2(-radius * 0.1, radius * 0.1)), max(2, int(radius * 0.18)))
            pygame.draw.circle(surface, (120, 114, 108, 54), self._point(center + Vector2(radius * 0.2, -radius * 0.22)), max(2, int(radius * 0.12)))
        else:
            pygame.draw.circle(surface, (188, 182, 172, 46), self._point(center + Vector2(-radius * 0.18, radius * 0.12)), max(2, int(radius * 0.16)))

    def _draw_planet_halo(
        self,
        surface: pygame.Surface,
        screen_pos: tuple[int, int],
        planet_radius: int,
        body: CelestialBody,
    ) -> None:
        halo_alpha = 10 if body.name in {"Mercury", "Venus", "Earth", "Mars"} else 16
        halo_radius = int(planet_radius * 2.1)
        halo_surface = pygame.Surface((halo_radius * 2, halo_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo_surface, (*body.color, halo_alpha), (halo_radius, halo_radius), halo_radius)
        surface.blit(halo_surface, (screen_pos[0] - halo_radius, screen_pos[1] - halo_radius), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_saturn_rings(self, surface: pygame.Surface, center: tuple[int, int], radius: int, front: bool) -> None:
        ring_size = radius * 6
        ring_surface = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        if front:
            ring_surface.set_clip(pygame.Rect(0, ring_size // 2, ring_size, ring_size // 2))
        else:
            ring_surface.set_clip(pygame.Rect(0, 0, ring_size, ring_size // 2))
        ellipse_rect = pygame.Rect(0, 0, ring_size, int(ring_size * 0.44))
        ellipse_rect.center = (ring_size // 2, ring_size // 2)

        for width_factor, alpha in ((0.2, 42), (0.14, 56), (0.08, 30)):
            line_width = max(1, int(radius * width_factor))
            color = (208, 194, 164, alpha)
            pygame.draw.ellipse(ring_surface, color, ellipse_rect, line_width)

        ring_surface.set_clip(None)
        surface.blit(ring_surface, (center[0] - ring_size // 2, center[1] - ring_size // 2), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_atmosphere(
        self,
        surface: pygame.Surface,
        center: Vector2,
        radius: int,
        body: CelestialBody,
        light_vector: Vector2,
    ) -> None:
        atmosphere_colors = {
            "Venus": (235, 212, 176, 48),
            "Earth": (134, 176, 229, 62),
            "Mars": (216, 168, 138, 28),
            "Uranus": (190, 228, 238, 46),
            "Neptune": (136, 172, 232, 54),
        }
        if body.name not in atmosphere_colors:
            return

        atmosphere_surface = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
        local_center = Vector2(atmosphere_surface.get_width() / 2, atmosphere_surface.get_height() / 2)
        halo_center = local_center + light_vector * radius * 0.18
        pygame.draw.circle(atmosphere_surface, atmosphere_colors[body.name], self._point(halo_center), int(radius * 1.18))
        pygame.draw.circle(atmosphere_surface, (255, 255, 255, 18), self._point(local_center + light_vector * radius * 0.34), max(2, int(radius * 0.95)), 1)
        surface.blit(
            atmosphere_surface,
            (int(center.x - atmosphere_surface.get_width() / 2), int(center.y - atmosphere_surface.get_height() / 2)),
            special_flags=pygame.BLEND_ALPHA_SDL2,
        )

    def _darken(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(channel * factor))) for channel in color)

    def _lighten(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(channel * factor))) for channel in color)

    def _point(self, vector: Vector2) -> tuple[int, int]:
        return int(vector.x), int(vector.y)

    def _draw_solar_corona(
        self,
        surface: pygame.Surface,
        center: Vector2,
        glow_size: int,
        elapsed_time: float,
    ) -> None:
        for index in range(18):
            angle = tau * index / 18 + elapsed_time * 0.025
            arm_length = glow_size * (0.18 + 0.04 * sin(elapsed_time * 0.4 + index))
            tip = center + Vector2(cos(angle), sin(angle)) * arm_length
            pygame.draw.line(
                surface,
                (255, 208, 132, 16),
                self._point(center),
                self._point(tip),
                max(1, glow_size // 80),
            )

    def _draw_solar_disc(
        self,
        surface: pygame.Surface,
        center: Vector2,
        radius: int,
        elapsed_time: float,
    ) -> None:
        pygame.draw.circle(surface, (250, 220, 158, 210), self._point(center), int(radius * 1.18))
        pygame.draw.circle(surface, STAR_GLOW, self._point(center), radius)
        pygame.draw.circle(surface, STAR_CORE, self._point(center), int(radius * 0.72))

        for index in range(16):
            angle = tau * index / 16 + elapsed_time * 0.05
            distance = radius * (0.14 + 0.22 * ((index % 3) / 3))
            granule_center = center + Vector2(cos(angle), sin(angle)) * distance
            granule_radius = max(2, int(radius * (0.08 + 0.03 * sin(index + elapsed_time * 0.3))))
            color = (255, 243, 214, 34 + (index % 4) * 14)
            pygame.draw.circle(surface, color, self._point(granule_center), granule_radius)

    def draw_labels(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        selected_body: CelestialBody | None,
    ) -> None:
        sun_center = camera.layout.scene_center
        for body in bodies:
            planet_position = camera.body_position(body)
            direction = body.direction()
            planet_radius = camera.planet_radius(body)
            anchor = planet_position + direction * (planet_radius + 12 * camera.layout.ui_scale)
            font = self.selected_label_font if body is selected_body else self.label_font
            color = (226, 231, 237) if body is selected_body else (142, 150, 163)
            label_surface = font.render(body.name, True, color)

            if anchor.x >= sun_center.x:
                label_position = (int(anchor.x + 6 * camera.layout.ui_scale), int(anchor.y - label_surface.get_height() / 2))
                line_end = (label_position[0] - int(4 * camera.layout.ui_scale), int(anchor.y))
            else:
                label_position = (
                    int(anchor.x - label_surface.get_width() - 6 * camera.layout.ui_scale),
                    int(anchor.y - label_surface.get_height() / 2),
                )
                line_end = (label_position[0] + label_surface.get_width() + int(4 * camera.layout.ui_scale), int(anchor.y))

            pygame.draw.line(surface, (94, 104, 120), self._point(planet_position), line_end, 1)
            surface.blit(label_surface, label_position)

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.label_scale) < 0.01:
            return

        self.label_scale = ui_scale
        self.label_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
        self.selected_label_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)), bold=True)
