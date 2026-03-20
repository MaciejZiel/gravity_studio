from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from pygame import Vector2


@dataclass
class CelestialBody:
    name: str
    angular_speed: float
    rotation_hours: float
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

    def reset(self) -> None:
        self.angle = self.starting_angle
