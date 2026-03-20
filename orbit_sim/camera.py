from __future__ import annotations

from dataclasses import dataclass
from math import log1p

from pygame import Vector2

from orbit_sim.config import REFERENCE_HEIGHT
from orbit_sim.models import CelestialBody


MAX_SOLAR_DISTANCE_AU = 30.05
EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class CameraLayout:
    viewport: tuple[int, int]
    ui_scale: float
    scene_center: Vector2
    inner_orbit_radius: float
    orbit_span: float


class SolarCamera:
    def __init__(self, viewport: tuple[int, int]) -> None:
        self.viewport = viewport
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.scale_mode = "compressed"
        self.layout = self._build_layout()

    def set_viewport(self, viewport: tuple[int, int]) -> None:
        self.viewport = viewport
        self.layout = self._build_layout()

    def update(self, dt: float) -> None:
        self.zoom += (self.target_zoom - self.zoom) * min(1.0, dt * 7.5)

    def adjust_zoom(self, delta: float) -> None:
        self.target_zoom = max(0.72, min(2.2, self.target_zoom + delta))

    def toggle_scale_mode(self) -> None:
        self.scale_mode = "expanded" if self.scale_mode == "compressed" else "compressed"

    def body_position(self, body: CelestialBody) -> Vector2:
        return self.layout.scene_center + body.direction() * self.orbit_radius(body)

    def orbit_radius(self, body: CelestialBody) -> float:
        compression = 2.2 if self.scale_mode == "compressed" else 1.15
        normalized = log1p(body.distance_au * compression) / log1p(MAX_SOLAR_DISTANCE_AU * compression)
        return (self.layout.inner_orbit_radius + normalized * self.layout.orbit_span) * self.zoom

    def planet_radius(self, body: CelestialBody) -> float:
        earth_radii = body.radius_km / EARTH_RADIUS_KM
        scale = 0.94 + (self.zoom - 1.0) * 0.18
        return max(3.0, (3.1 + 4.6 * (earth_radii ** 0.41)) * self.layout.ui_scale * scale)

    def sun_radius(self) -> float:
        width, height = self.viewport
        base = min(width, height) * 0.015
        return max(18.0, base * (0.92 + (self.zoom - 1.0) * 0.12))

    def _build_layout(self) -> CameraLayout:
        width, height = self.viewport
        ui_scale = max(0.74, min(1.55, height / REFERENCE_HEIGHT))
        scene_center = Vector2(width * 0.44, height * 0.54)
        inner_orbit_radius = 48 * ui_scale
        orbit_span = min(width * 0.36, height * 0.46)
        return CameraLayout(
            viewport=self.viewport,
            ui_scale=ui_scale,
            scene_center=scene_center,
            inner_orbit_radius=inner_orbit_radius,
            orbit_span=orbit_span,
        )
