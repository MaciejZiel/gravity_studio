from __future__ import annotations

from datetime import datetime
from math import cos, sin, tau

import pygame
from pygame import Vector2

from orbit_sim.camera import SolarCamera
from orbit_sim.config import SPACE_HAZE, STAR_CORE, STAR_GLOW
from orbit_sim.missions import MISSION_DEFINITIONS, MissionDefinition
from orbit_sim.models import CelestialBody, MoonBody
from orbit_sim.planet_sphere import SpinningPlanetRenderer
from orbit_sim.planet_textures import PlanetTextureLibrary


class SceneRenderer:
    def __init__(self) -> None:
        self.label_scale = 0.0
        self.label_font: pygame.font.Font | None = None
        self.selected_label_font: pygame.font.Font | None = None
        self.focus_renderer = SpinningPlanetRenderer()
        self.texture_library = PlanetTextureLibrary()
        self._space_haze_cache: dict[tuple[tuple[int, int], float], pygame.Surface] = {}
        self._halo_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._ring_cache: dict[tuple[int, bool], pygame.Surface] = {}
        self._label_text_cache: dict[tuple[int, str, tuple[int, int, int]], pygame.Surface] = {}

    def draw(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        moons: list[MoonBody],
        elapsed_time: float,
        simulation_days: float,
        current_time: datetime,
        hovered_body: CelestialBody | None,
        selected_body: CelestialBody | None,
        show_orbits: bool,
        show_labels: bool,
        show_missions: bool,
        focus_rotation_degrees: float = 0.0,
    ) -> None:
        self._ensure_fonts(camera.layout.ui_scale)
        self.draw_space_haze(surface, camera.zoom)
        if show_orbits:
            self.draw_orbits(surface, camera, bodies, selected_body)
        if show_missions:
            self.draw_missions(surface, camera, current_time, selected_body)
        self.draw_star(surface, camera, elapsed_time)
        self.draw_planets(surface, camera, bodies, elapsed_time, hovered_body, selected_body)
        self.draw_moons(surface, camera, bodies, moons, selected_body)
        if show_labels:
            self.draw_labels(surface, camera, bodies, selected_body)
        if camera.scene_mode == "focus" and selected_body is not None:
            self.draw_focus_vignette(surface, camera, selected_body)
        if selected_body is not None and self._should_draw_focus_closeup(camera):
            self.draw_focus_closeup(surface, camera, selected_body, moons, simulation_days, focus_rotation_degrees)

    def draw_space_haze(self, surface: pygame.Surface, zoom: float) -> None:
        cache_key = (surface.get_size(), round(zoom, 2))
        if cache_key not in self._space_haze_cache:
            size = surface.get_size()
            haze = pygame.Surface(size, pygame.SRCALPHA)
            center = (int(size[0] * 0.44), int(size[1] * 0.54))
            haze_scale = 0.9 + (zoom - 1.0) * 0.18

            min_dimension = min(size)
            for radius_factor, alpha in ((0.5, 9), (0.32, 18), (0.2, 28)):
                radius = int(min_dimension * radius_factor)
                pygame.draw.circle(haze, (*SPACE_HAZE, alpha), center, int(radius * haze_scale))
            if len(self._space_haze_cache) > 24:
                self._space_haze_cache.clear()
            self._space_haze_cache[cache_key] = haze

        surface.blit(self._space_haze_cache[cache_key], (0, 0))

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

        for body in bodies:
            base_color = (112, 121, 138, 24)
            if body is selected_body:
                base_color = (194, 203, 214, 52)

            orbit_points = [self._point(point) for point in camera.project_orbit_points(body, steps=160)]
            if len(orbit_points) > 2:
                pygame.draw.aalines(orbit_surface, base_color, False, orbit_points)

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
        for body in sorted(bodies, key=camera.body_depth):
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

    def draw_moons(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        moons: list[MoonBody],
        selected_body: CelestialBody | None,
    ) -> None:
        if not moons:
            return

        parent_lookup = {body.name: body for body in bodies}
        for moon in moons:
            parent = parent_lookup.get(moon.parent_name)
            if parent is None or not self._should_draw_moon(parent, selected_body, camera):
                continue

            parent_position = camera.body_position(parent)
            parent_radius = max(3, int(camera.planet_radius(parent)))
            orbit_radius = self._moon_orbit_radius(parent, parent_radius, moon, camera)
            orbit_rect = pygame.Rect(0, 0, orbit_radius * 2, max(2, int(orbit_radius * 0.54)))
            orbit_rect.center = self._point(parent_position)
            pygame.draw.ellipse(surface, (102, 112, 130, 42), orbit_rect, 1)

            moon_offset = moon.orbital_offset()
            moon_position = parent_position + Vector2(moon_offset.x * orbit_radius, moon_offset.y * orbit_rect.height * 0.5)
            moon_radius = self._moon_radius(parent_radius, moon)
            pygame.draw.circle(surface, (*moon.color, 228), self._point(moon_position), moon_radius)
            pygame.draw.circle(surface, (*moon.accent_color, 128), self._point(moon_position + Vector2(-moon_radius * 0.28, -moon_radius * 0.18)), max(1, moon_radius - 1))
            pygame.draw.circle(surface, (238, 242, 246), self._point(moon_position + Vector2(moon_radius * 0.36, moon_radius * 0.18)), 1)

    def draw_missions(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        current_time: datetime,
        selected_body: CelestialBody | None,
    ) -> None:
        mission_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for mission in MISSION_DEFINITIONS:
            if mission.frame == "earth_local" and (selected_body is None or selected_body.name != "Earth"):
                continue

            path = self._mission_points(camera, mission, selected_body)
            if len(path) < 2:
                continue

            alpha = 118 if mission.frame == "heliocentric" else 164
            pygame.draw.aalines(mission_layer, (*mission.color, alpha), False, path)
            marker = self._mission_marker(path, mission, current_time)
            pygame.draw.circle(mission_layer, (*mission.color, 228), marker, 4 if mission.frame == "heliocentric" else 5)
            label = self._label_surface(self.label_font, mission.label, (208, 216, 226))
            label_pos = (marker[0] + 10, marker[1] - label.get_height() // 2)
            mission_layer.blit(label, label_pos)

        surface.blit(mission_layer, (0, 0))

    def _mission_points(
        self,
        camera: SolarCamera,
        mission: MissionDefinition,
        selected_body: CelestialBody | None,
    ) -> list[tuple[int, int]]:
        if mission.frame == "heliocentric":
            return [self._point(camera.project_space_point(pygame.Vector3(x, y, 0.0))) for x, y in mission.path_points]

        if selected_body is None:
            return []

        parent_position = camera.body_position(selected_body)
        scale = max(36.0, camera.planet_radius(selected_body) * 5.8)
        return [
            self._point(parent_position + Vector2(point[0] * scale, point[1] * scale))
            for point in mission.path_points
        ]

    def _mission_marker(
        self,
        path: list[tuple[int, int]],
        mission: MissionDefinition,
        current_time: datetime,
    ) -> tuple[int, int]:
        total = (mission.progress_end - mission.launch).total_seconds()
        if total <= 0:
            return path[-1]

        elapsed = (current_time - mission.launch).total_seconds()
        progress = max(0.0, min(1.0, elapsed / total))
        return self._interpolate_polyline(path, progress)

    def _interpolate_polyline(self, points: list[tuple[int, int]], progress: float) -> tuple[int, int]:
        if len(points) == 1:
            return points[0]

        segment_lengths = []
        total_length = 0.0
        for start, end in zip(points, points[1:]):
            length = Vector2(end).distance_to(Vector2(start))
            segment_lengths.append(length)
            total_length += length

        target = total_length * progress
        traversed = 0.0
        for index, length in enumerate(segment_lengths):
            if traversed + length >= target and length > 0:
                local = (target - traversed) / length
                start = Vector2(points[index])
                end = Vector2(points[index + 1])
                point = start.lerp(end, local)
                return int(point.x), int(point.y)
            traversed += length

        return points[-1]

    def _should_draw_moon(
        self,
        parent: CelestialBody,
        selected_body: CelestialBody | None,
        camera: SolarCamera,
    ) -> bool:
        if camera.scene_mode == "focus":
            return parent is selected_body
        if parent is selected_body:
            return True
        if camera.zoom >= 1.34 and parent.name in {"Earth", "Jupiter", "Saturn"}:
            return True
        return False

    def _moon_orbit_radius(
        self,
        parent: CelestialBody,
        parent_radius: int,
        moon: MoonBody,
        camera: SolarCamera,
    ) -> int:
        ratio = moon.orbital_distance_km / max(parent.radius_km, 1.0)
        base = parent_radius * (1.7 + min(4.8, ratio ** 0.32))
        if camera.scene_mode == "focus" and parent is camera.focus_body:
            base *= 1.24
        return int(base)

    def _moon_radius(self, parent_radius: int, moon: MoonBody) -> int:
        size_ratio = (moon.radius_km / 1737.4) ** 0.36
        return max(2, int(parent_radius * 0.16 * size_ratio))

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
        if body.has_rings:
            self._draw_ring_shadow(surface, center, radius)

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
        halo_radius = int(planet_radius * 2.1)
        halo_surface = self._planet_halo_surface(body, halo_radius)
        surface.blit(halo_surface, (screen_pos[0] - halo_radius, screen_pos[1] - halo_radius), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_saturn_rings(self, surface: pygame.Surface, center: tuple[int, int], radius: int, front: bool) -> None:
        ring_surface = self._saturn_ring_surface(radius, front)
        ring_size = ring_surface.get_width()
        surface.blit(ring_surface, (center[0] - ring_size // 2, center[1] - ring_size // 2), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _planet_halo_surface(self, body: CelestialBody, halo_radius: int) -> pygame.Surface:
        cache_key = (body.name, halo_radius)
        if cache_key not in self._halo_cache:
            halo_alpha = 10 if body.name in {"Mercury", "Venus", "Earth", "Mars"} else 16
            halo_surface = pygame.Surface((halo_radius * 2, halo_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo_surface, (*body.color, halo_alpha), (halo_radius, halo_radius), halo_radius)
            self._halo_cache[cache_key] = halo_surface
        return self._halo_cache[cache_key]

    def _saturn_ring_surface(self, radius: int, front: bool) -> pygame.Surface:
        cache_key = (radius, front)
        if cache_key in self._ring_cache:
            return self._ring_cache[cache_key]

        ring_size = radius * 6
        ring_surface = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        if front:
            ring_surface.set_clip(pygame.Rect(0, ring_size // 2, ring_size, ring_size // 2))
        else:
            ring_surface.set_clip(pygame.Rect(0, 0, ring_size, ring_size // 2))
        ellipse_rect = pygame.Rect(0, 0, ring_size, int(ring_size * 0.44))
        ellipse_rect.center = (ring_size // 2, ring_size // 2)
        alpha_texture = self.texture_library.auxiliary_texture("saturn_ring_alpha", (512, 32))

        if alpha_texture is not None:
            max_band = max(14, ring_size // 12)
            inner_width = ellipse_rect.width * 0.42
            outer_width = ellipse_rect.width * 0.96
            for index in range(max_band):
                t = index / max(1, max_band - 1)
                alpha_sample = alpha_texture.get_at((min(alpha_texture.get_width() - 1, int(t * (alpha_texture.get_width() - 1))), alpha_texture.get_height() // 2))
                alpha = max(10, int(alpha_sample.a * (0.22 if front else 0.16)))
                band_width = int(inner_width + (outer_width - inner_width) * t)
                ring_rect = pygame.Rect(0, 0, band_width, max(2, int(ellipse_rect.height * (0.64 + 0.18 * t))))
                ring_rect.center = ellipse_rect.center
                tint = (
                    int(194 + 22 * t),
                    int(180 + 18 * sin(t * 9.0)),
                    int(152 + 20 * cos(t * 6.0)),
                    alpha,
                )
                pygame.draw.ellipse(ring_surface, tint, ring_rect, max(1, ring_size // 140))
        else:
            for width_factor, alpha in ((0.2, 42), (0.14, 56), (0.08, 30)):
                line_width = max(1, int(radius * width_factor))
                color = (208, 194, 164, alpha)
                pygame.draw.ellipse(ring_surface, color, ellipse_rect, line_width)

        ring_surface.set_clip(None)
        self._ring_cache[cache_key] = ring_surface
        return ring_surface

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

    def _draw_ring_shadow(self, surface: pygame.Surface, center: Vector2, radius: int) -> None:
        shadow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(0, 0, int(radius * 2.4), max(2, int(radius * 0.42)))
        shadow_rect.center = (shadow_surface.get_width() // 2, shadow_surface.get_height() // 2 - int(radius * 0.08))
        pygame.draw.ellipse(shadow_surface, (44, 36, 24, 52), shadow_rect)
        pygame.draw.ellipse(shadow_surface, (22, 18, 12, 36), shadow_rect.inflate(int(radius * 0.2), int(radius * 0.12)))
        surface.blit(
            shadow_surface,
            (int(center.x - shadow_surface.get_width() / 2), int(center.y - shadow_surface.get_height() / 2)),
            special_flags=pygame.BLEND_ALPHA_SDL2,
        )

    def _darken(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(channel * factor))) for channel in color)

    def _lighten(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(channel * factor))) for channel in color)

    def _point(self, vector: Vector2) -> tuple[int, int]:
        return int(vector.x), int(vector.y)

    def draw_focus_vignette(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        selected_body: CelestialBody,
    ) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 78))
        center = camera.body_position(selected_body)
        for radius_factor, alpha in ((10.5, 0), (8.0, 22), (5.8, 46)):
            pygame.draw.circle(
                overlay,
                (0, 0, 0, alpha),
                self._point(center),
                int(camera.planet_radius(selected_body) * radius_factor),
            )

        surface.blit(overlay, (0, 0))

    def draw_focus_closeup(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        selected_body: CelestialBody,
        moons: list[MoonBody],
        simulation_days: float,
        focus_rotation_degrees: float,
    ) -> None:
        hero_rect = self.focus_closeup_rect(surface.get_size(), camera)
        if hero_rect is None:
            return

        diameter = hero_rect.width

        shadow = pygame.Surface((diameter * 2, diameter * 2), pygame.SRCALPHA)
        shadow_rect = shadow.get_rect(center=hero_rect.center)
        pygame.draw.circle(
            shadow,
            (0, 0, 0, 98),
            (shadow.get_width() // 2, shadow.get_height() // 2 + int(diameter * 0.09)),
            int(diameter * 0.48),
        )
        surface.blit(shadow, shadow_rect.topleft, special_flags=pygame.BLEND_ALPHA_SDL2)

        sphere_surface = self.focus_renderer.render(
            selected_body,
            diameter,
            simulation_days,
            display_rotation_degrees=focus_rotation_degrees,
        )
        if sphere_surface is not None:
            glow = pygame.Surface((diameter * 2, diameter * 2), pygame.SRCALPHA)
            glow_center = Vector2(glow.get_width() / 2, glow.get_height() / 2)
            for radius_factor, alpha in ((0.66, 10), (0.58, 14), (0.48, 18)):
                pygame.draw.circle(
                    glow,
                    (*selected_body.color, alpha),
                    self._point(glow_center),
                    int(diameter * radius_factor),
                )
            flare_center = glow_center + Vector2(-diameter * 0.12, -diameter * 0.08)
            pygame.draw.circle(
                glow,
                (*selected_body.accent_color, 20 if selected_body.name in {"Earth", "Venus", "Neptune"} else 12),
                self._point(flare_center),
                int(diameter * 0.38),
            )
            surface.blit(glow, glow.get_rect(center=hero_rect.center).topleft, special_flags=pygame.BLEND_ALPHA_SDL2)
            if selected_body.has_rings:
                self._draw_saturn_rings(surface, hero_rect.center, diameter // 2, front=False)
            surface.blit(sphere_surface, hero_rect.topleft)
            if selected_body.has_rings:
                self._draw_saturn_rings(surface, hero_rect.center, diameter // 2, front=True)
            self._draw_focus_satellites(surface, hero_rect, selected_body, moons)
        else:
            fallback_surface = pygame.Surface((diameter * 2, diameter * 2), pygame.SRCALPHA)
            center = Vector2(fallback_surface.get_width() / 2, fallback_surface.get_height() / 2)
            light_vector = Vector2(-0.75, -0.28).normalize()
            self._draw_planet_sprite(fallback_surface, center, diameter // 2, selected_body, light_vector)
            surface.blit(fallback_surface, fallback_surface.get_rect(center=hero_rect.center))

    def _draw_focus_satellites(
        self,
        surface: pygame.Surface,
        hero_rect: pygame.Rect,
        selected_body: CelestialBody,
        moons: list[MoonBody],
    ) -> None:
        focus_moons = [moon for moon in moons if moon.parent_name == selected_body.name]
        if not focus_moons:
            return

        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        hero_center = Vector2(hero_rect.center)
        base_radius = hero_rect.width * 0.68
        for index, moon in enumerate(focus_moons):
            orbit_radius = int(base_radius + index * hero_rect.width * 0.12)
            orbit_rect = pygame.Rect(0, 0, orbit_radius * 2, int(orbit_radius * 0.54))
            orbit_rect.center = hero_rect.center
            pygame.draw.ellipse(layer, (94, 106, 126, 58), orbit_rect, 1)
            moon_offset = moon.orbital_offset()
            moon_position = hero_center + Vector2(moon_offset.x * orbit_radius, moon_offset.y * orbit_rect.height * 0.5)
            moon_radius = max(3, int(hero_rect.width * 0.028 * (moon.radius_km / 1737.4) ** 0.3))
            pygame.draw.circle(layer, (*moon.color, 236), self._point(moon_position), moon_radius)
            pygame.draw.circle(layer, (*moon.accent_color, 182), self._point(moon_position + Vector2(-moon_radius * 0.3, -moon_radius * 0.16)), max(1, moon_radius - 1))
            tag = self._label_surface(self.label_font, moon.name, (214, 220, 230))
            layer.blit(tag, (int(moon_position.x + moon_radius + 8), int(moon_position.y - tag.get_height() / 2)))

        surface.blit(layer, (0, 0))

    def focus_closeup_rect(self, surface_size: tuple[int, int], camera: SolarCamera) -> pygame.Rect | None:
        if not self._should_draw_focus_closeup(camera):
            return None

        viewport_min = min(surface_size)
        base_diameter = viewport_min * (0.24 if camera.scene_mode == "focus" else 0.18)
        zoom_lift = max(0.0, camera.zoom - 1.0) * viewport_min * 0.03
        diameter = int(max(180, min(viewport_min * 0.34, base_diameter + zoom_lift)))
        hero_center = Vector2(surface_size[0] * 0.24, surface_size[1] * 0.57)
        hero_rect = pygame.Rect(0, 0, diameter, diameter)
        hero_rect.center = self._point(hero_center)
        return hero_rect

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

    def _should_draw_focus_closeup(self, camera: SolarCamera) -> bool:
        return camera.scene_mode == "focus" or camera.zoom >= 1.65

    def draw_labels(
        self,
        surface: pygame.Surface,
        camera: SolarCamera,
        bodies: list[CelestialBody],
        selected_body: CelestialBody | None,
    ) -> None:
        label_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        sun_center = camera.layout.scene_center
        left_candidates: list[dict[str, object]] = []
        right_candidates: list[dict[str, object]] = []

        for body in bodies:
            alpha = self._label_alpha(body, camera, selected_body)
            if alpha <= 0:
                continue

            planet_position = camera.body_position(body)
            direction = body.direction()
            planet_radius = camera.planet_radius(body)
            anchor = planet_position + direction * (planet_radius + 12 * camera.layout.ui_scale)
            font = self.selected_label_font if body is selected_body else self.label_font
            color = (226, 231, 237) if body is selected_body else (142, 150, 163)
            label_surface = self._label_surface(font, body.name, color)
            label_surface.set_alpha(alpha)
            side = "right" if anchor.x >= sun_center.x else "left"
            candidate = {
                "body": body,
                "planet_position": planet_position,
                "anchor": anchor,
                "label_surface": label_surface,
                "alpha": alpha,
                "side": side,
                "preferred_y": int(anchor.y - label_surface.get_height() / 2),
            }
            if side == "right":
                right_candidates.append(candidate)
            else:
                left_candidates.append(candidate)

        for side_candidates in (left_candidates, right_candidates):
            self._resolve_label_stack(side_candidates, surface.get_height(), camera.layout.ui_scale)

        for candidate in [*left_candidates, *right_candidates]:
            label_surface = candidate["label_surface"]
            anchor = candidate["anchor"]
            planet_position = candidate["planet_position"]
            alpha = candidate["alpha"]
            label_y = candidate["resolved_y"]
            if candidate["side"] == "right":
                label_position = (int(anchor.x + 6 * camera.layout.ui_scale), label_y)
                line_end = (label_position[0] - int(4 * camera.layout.ui_scale), label_y + label_surface.get_height() // 2)
            else:
                label_position = (
                    int(anchor.x - label_surface.get_width() - 6 * camera.layout.ui_scale),
                    label_y,
                )
                line_end = (
                    label_position[0] + label_surface.get_width() + int(4 * camera.layout.ui_scale),
                    label_y + label_surface.get_height() // 2,
                )

            pygame.draw.line(label_layer, (94, 104, 120, alpha), self._point(planet_position), line_end, 1)
            label_layer.blit(label_surface, label_position)

        surface.blit(label_layer, (0, 0))

    def _resolve_label_stack(
        self,
        candidates: list[dict[str, object]],
        surface_height: int,
        ui_scale: float,
    ) -> None:
        if not candidates:
            return

        candidates.sort(key=lambda item: int(item["preferred_y"]))
        gap = int(8 * ui_scale)
        min_y = int(24 * ui_scale)
        max_y = surface_height - int(28 * ui_scale)

        current_y = min_y
        for candidate in candidates:
            label_surface = candidate["label_surface"]
            height = label_surface.get_height()
            preferred_y = max(min_y, min(int(candidate["preferred_y"]), max_y - height))
            resolved_y = max(preferred_y, current_y)
            candidate["resolved_y"] = resolved_y
            current_y = resolved_y + height + gap

        overflow = current_y - max_y
        if overflow <= 0:
            return

        for candidate in reversed(candidates):
            if overflow <= 0:
                break
            label_surface = candidate["label_surface"]
            shift = min(overflow, max(0, int(candidate["resolved_y"]) - min_y))
            candidate["resolved_y"] = int(candidate["resolved_y"]) - shift
            overflow -= shift

    def _ensure_fonts(self, ui_scale: float) -> None:
        if abs(ui_scale - self.label_scale) < 0.01:
            return

        self.label_scale = ui_scale
        self._label_text_cache.clear()
        self.label_font = pygame.font.SysFont("segoeui", max(11, int(12 * ui_scale)))
        self.selected_label_font = pygame.font.SysFont("segoeui", max(12, int(13 * ui_scale)), bold=True)

    def _label_surface(
        self,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        cache_key = (id(font), text, color)
        if cache_key not in self._label_text_cache:
            self._label_text_cache[cache_key] = font.render(text, True, color)
        return self._label_text_cache[cache_key].copy()

    def _label_alpha(
        self,
        body: CelestialBody,
        camera: SolarCamera,
        selected_body: CelestialBody | None,
    ) -> int:
        if body is selected_body:
            return 255

        if camera.scene_mode == "focus":
            return 0

        if camera.scene_mode == "inner_worlds":
            return 210 if body.name in {"Mercury", "Venus", "Earth", "Mars"} else 0

        if camera.scene_mode == "outer_worlds":
            return 210 if body.name in {"Jupiter", "Saturn", "Uranus", "Neptune"} else 0

        if camera.zoom < 1.08:
            return 190 if body.name in {"Earth", "Mars", "Jupiter", "Saturn", "Neptune"} else 0

        if camera.zoom < 1.28:
            return 190 if body.name != "Mercury" else 0

        return 210
