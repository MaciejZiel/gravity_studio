from __future__ import annotations

from dataclasses import dataclass
from math import cos, log1p, radians, sin

from pygame import Vector2, Vector3

from orbit_sim.config import REFERENCE_HEIGHT
from orbit_sim.models import CelestialBody


MAX_SOLAR_DISTANCE_AU = 30.05
EARTH_RADIUS_KM = 6371.0
VIEW_TILT_DEG = 24.0
STORY_COMPRESSION = 0.14
STORY_SPAN_FACTOR = 1.22


@dataclass(frozen=True)
class ScenePreset:
    label: str
    center_ratio: tuple[float, float]
    scene_zoom: float
    compression: float
    orbit_span_factor: float


SCENE_PRESETS = {
    "full_system": ScenePreset("System", (0.44, 0.54), 1.0, 2.15, 1.0),
    "inner_worlds": ScenePreset("Inner", (0.42, 0.56), 1.42, 5.3, 1.08),
    "gas_giants": ScenePreset("Giants", (0.5, 0.56), 1.32, 1.02, 1.12),
    "outer_worlds": ScenePreset("Outer", (0.48, 0.55), 1.18, 0.92, 1.14),
    "focus": ScenePreset("Focus", (0.46, 0.56), 1.82, 1.28, 1.08),
}


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
        self.user_zoom = 1.0
        self.target_user_zoom = 1.0
        self.scene_zoom = 1.0
        self.target_scene_zoom = 1.0
        self.zoom = 1.0
        self.scale_mode = "compressed"
        self.scene_mode = "full_system"
        self.focus_body: CelestialBody | None = None
        self.scale_story_mode = False
        self.story_progress = 0.0
        self.target_story_progress = 0.0
        self.current_compression = self._scene_preset.compression
        self.target_compression = self.current_compression
        self.current_span_factor = self._scene_preset.orbit_span_factor
        self.target_span_factor = self.current_span_factor
        self.current_center = self._base_scene_center(self._scene_preset)
        self.target_center = self.current_center
        self.transition_energy = 0.0
        self.layout = self._build_layout(self.current_center, self.current_span_factor)
        self._body_state_cache: dict[str, tuple[Vector2, float]] = {}
        self._orbit_cache: dict[tuple[str, int, int, float, float, float], list[Vector2]] = {}

    def set_viewport(self, viewport: tuple[int, int]) -> None:
        self.viewport = viewport
        self.current_center = self._base_scene_center(self._scene_preset)
        self.target_center = self.current_center
        self.layout = self._build_layout(self.current_center, self.current_span_factor)
        self._orbit_cache.clear()

    @property
    def _scene_preset(self) -> ScenePreset:
        return SCENE_PRESETS[self.scene_mode]

    @property
    def scene_label(self) -> str:
        return self._scene_preset.label

    @property
    def background_parallax(self) -> Vector2:
        base = self._base_scene_center(self._scene_preset)
        return (self.current_center - base) * 0.22

    def adjust_zoom(self, delta: float) -> None:
        self.target_user_zoom = max(0.72, min(2.45, self.target_user_zoom + delta))

    def toggle_scale_mode(self) -> None:
        self.scale_mode = "expanded" if self.scale_mode == "compressed" else "compressed"

    def set_scale_story(self, enabled: bool) -> None:
        self.scale_story_mode = enabled
        self.target_story_progress = 1.0 if enabled else 0.0

    def set_scene(self, scene_mode: str) -> None:
        if scene_mode not in SCENE_PRESETS:
            return

        if scene_mode != "focus":
            self.focus_body = None
        elif self.focus_body is None:
            return

        if self.scene_mode != scene_mode:
            self.transition_energy = 1.0
        self.scene_mode = scene_mode

    def set_focus_body(self, body: CelestialBody | None) -> None:
        if self.focus_body is not body:
            self.transition_energy = 1.0
        self.focus_body = body
        self.scene_mode = "focus" if body is not None else "full_system"

    def reset(self) -> None:
        self.user_zoom = 1.0
        self.target_user_zoom = 1.0
        self.scene_zoom = 1.0
        self.target_scene_zoom = 1.0
        self.scene_mode = "full_system"
        self.focus_body = None
        self.scale_story_mode = False
        self.story_progress = 0.0
        self.target_story_progress = 0.0
        self.current_compression = SCENE_PRESETS["full_system"].compression
        self.target_compression = self.current_compression
        self.current_span_factor = SCENE_PRESETS["full_system"].orbit_span_factor
        self.target_span_factor = self.current_span_factor
        self.current_center = self._base_scene_center(SCENE_PRESETS["full_system"])
        self.target_center = self.current_center
        self.transition_energy = 0.0
        self.zoom = 1.0
        self.layout = self._build_layout(self.current_center, self.current_span_factor)
        self._body_state_cache.clear()
        self._orbit_cache.clear()

    def update(self, dt: float, elapsed_time: float) -> None:
        preset = self._scene_preset
        self.target_scene_zoom = preset.scene_zoom
        base_compression = preset.compression * (1.0 if self.scale_mode == "compressed" else 0.62)
        base_span_factor = preset.orbit_span_factor * (1.02 if self.scale_mode == "expanded" else 1.0)
        self.story_progress += (self.target_story_progress - self.story_progress) * min(1.0, dt * 2.1)
        self.target_compression = base_compression + (STORY_COMPRESSION - base_compression) * self.story_progress
        self.target_span_factor = base_span_factor + (STORY_SPAN_FACTOR - base_span_factor) * self.story_progress
        self.target_center = self._target_scene_center(preset, elapsed_time)
        self.transition_energy = max(0.0, self.transition_energy - dt * 1.6)

        follow_strength = min(1.0, dt * 4.8)
        zoom_strength = min(1.0, dt * 5.4)
        self.current_center += (self.target_center - self.current_center) * follow_strength
        self.scene_zoom += (self.target_scene_zoom - self.scene_zoom) * zoom_strength
        self.user_zoom += (self.target_user_zoom - self.user_zoom) * zoom_strength
        self.current_compression += (self.target_compression - self.current_compression) * min(1.0, dt * 4.0)
        self.current_span_factor += (self.target_span_factor - self.current_span_factor) * min(1.0, dt * 4.0)
        self.zoom = self.user_zoom * self.scene_zoom
        self.layout = self._build_layout(self.current_center, self.current_span_factor)
        self._body_state_cache.clear()
        if len(self._orbit_cache) > 96:
            self._orbit_cache.clear()

    def body_position(self, body: CelestialBody) -> Vector2:
        return self.layout.scene_center + self.project_orbital_offset(body)

    def body_depth(self, body: CelestialBody) -> float:
        return self.projected_body_state(body)[1]

    def project_orbit_points(self, body: CelestialBody, steps: int = 180) -> list[Vector2]:
        cache_key = (
            body.name,
            steps,
            self.viewport[1],
            round(self.zoom, 3),
            round(self.current_compression, 3),
            round(self.current_span_factor, 3),
        )
        if cache_key not in self._orbit_cache:
            points: list[Vector2] = []
            for index in range(steps + 1):
                angle = (index / steps) * 6.283185307179586
                projected = self._project_body_vector(
                    body.orbital_position(angle),
                    self.zoom,
                    self.current_compression,
                    self.current_span_factor,
                )
                points.append(projected.xy)
            self._orbit_cache[cache_key] = points
        return [self.layout.scene_center + point for point in self._orbit_cache[cache_key]]

    def orbit_radius(self, body: CelestialBody) -> float:
        return self._orbit_radius_for_distance(body.distance_au, self.zoom, self.current_compression, self.current_span_factor)

    def planet_radius(self, body: CelestialBody) -> float:
        earth_radii = body.radius_km / EARTH_RADIUS_KM
        scale = 0.93 + (self.zoom - 1.0) * 0.12
        return max(3.0, (3.1 + 4.6 * (earth_radii ** 0.41)) * self.layout.ui_scale * scale)

    def sun_radius(self) -> float:
        width, height = self.viewport
        base = min(width, height) * 0.015
        return max(18.0, base * (0.92 + (self.zoom - 1.0) * 0.12))

    def _build_layout(self, scene_center: Vector2, orbit_span_factor: float) -> CameraLayout:
        width, height = self.viewport
        ui_scale = max(0.74, min(1.55, height / REFERENCE_HEIGHT))
        inner_orbit_radius = 48 * ui_scale
        orbit_span = min(width * 0.36, height * 0.46) * orbit_span_factor
        return CameraLayout(
            viewport=self.viewport,
            ui_scale=ui_scale,
            scene_center=scene_center,
            inner_orbit_radius=inner_orbit_radius,
            orbit_span=orbit_span,
        )

    def _target_scene_center(self, preset: ScenePreset, elapsed_time: float) -> Vector2:
        base_center = self._base_scene_center(preset)
        if self.scene_mode == "focus" and self.focus_body is not None:
            desired_anchor = Vector2(self.viewport[0] * 0.66, self.viewport[1] * 0.56)
            projected = self._project_body_vector(
                self.focus_body.orbital_position(),
                self.user_zoom * self.target_scene_zoom,
                self.target_compression,
                self.target_span_factor,
            )
            return desired_anchor - projected.xy

        drift_amount = 8.0 * self.layout.ui_scale
        drift = Vector2(
            sin(elapsed_time * 0.11) * drift_amount,
            sin(elapsed_time * 0.09 + 0.9) * drift_amount * 0.6,
        )
        cinematic = Vector2(
            sin(elapsed_time * 1.8 + 0.4) * 18.0 * self.layout.ui_scale,
            -16.0 * self.layout.ui_scale,
        ) * self.transition_energy
        return base_center + drift + cinematic

    def _base_scene_center(self, preset: ScenePreset) -> Vector2:
        return Vector2(self.viewport[0] * preset.center_ratio[0], self.viewport[1] * preset.center_ratio[1])

    def _orbit_radius_for_distance(
        self,
        distance_au: float,
        zoom: float,
        compression: float,
        orbit_span_factor: float,
    ) -> float:
        layout = self._build_layout(self.current_center, orbit_span_factor)
        normalized = log1p(distance_au * compression) / log1p(MAX_SOLAR_DISTANCE_AU * compression)
        return (layout.inner_orbit_radius + normalized * layout.orbit_span) * zoom

    def projected_body_state(self, body: CelestialBody) -> tuple[Vector2, float]:
        if body.name not in self._body_state_cache:
            projected = self._project_body_vector(body.orbital_position(), self.zoom, self.current_compression, self.current_span_factor)
            self._body_state_cache[body.name] = (self.layout.scene_center + projected.xy, projected.z)
        return self._body_state_cache[body.name]

    def project_orbital_offset(self, body: CelestialBody) -> Vector2:
        return self.projected_body_state(body)[0] - self.layout.scene_center

    def project_space_point(self, position: Vector3) -> Vector2:
        projected = self._project_body_vector(position, self.zoom, self.current_compression, self.current_span_factor)
        return self.layout.scene_center + projected.xy

    def _project_body_vector(
        self,
        orbital_position: Vector3,
        zoom: float,
        compression: float,
        orbit_span_factor: float,
    ) -> Vector3:
        distance = max(0.08, orbital_position.length())
        scale_radius = self._orbit_radius_for_distance(distance, zoom, compression, orbit_span_factor)
        scaled = orbital_position.normalize() * scale_radius if orbital_position.length_squared() > 0 else Vector3()
        tilt = radians(VIEW_TILT_DEG)
        projected_y = scaled.y * cos(tilt) - scaled.z * sin(tilt)
        depth = scaled.y * sin(tilt) + scaled.z * cos(tilt)
        return Vector3(scaled.x, projected_y, depth)
