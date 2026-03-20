from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

from pygame import Vector2, Vector3


@dataclass
class CelestialBody:
    name: str
    angular_speed: float
    rotation_hours: float
    eccentricity: float
    inclination_deg: float
    ascending_node_deg: float
    periapsis_deg: float
    axial_tilt_deg: float
    season_offset_deg: float
    color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    angle: float
    starting_angle: float
    radius_km: float
    distance_au: float
    orbital_period_days: float
    fact: str
    has_rings: bool = False

    def direction(self) -> Vector2:
        return Vector2(cos(self.angle), sin(self.angle))

    def orbital_position(self) -> Vector3:
        radial_distance = self.distance_au * (1.0 - self.eccentricity * self.eccentricity)
        radial_distance /= max(0.18, 1.0 + self.eccentricity * cos(self.angle - radians(self.periapsis_deg)))
        true_longitude = self.angle
        ascending_node = radians(self.ascending_node_deg)
        inclination = radians(self.inclination_deg)

        x = radial_distance * (
            cos(ascending_node) * cos(true_longitude)
            - sin(ascending_node) * sin(true_longitude) * cos(inclination)
        )
        y = radial_distance * (
            sin(ascending_node) * cos(true_longitude)
            + cos(ascending_node) * sin(true_longitude) * cos(inclination)
        )
        z = radial_distance * sin(true_longitude) * sin(inclination)
        return Vector3(x, y, z)

    def reset(self) -> None:
        self.angle = self.starting_angle
