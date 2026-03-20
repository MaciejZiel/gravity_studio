from __future__ import annotations

from math import tau

from orbit_sim.models import CelestialBody
from orbit_sim.solar_system import PlanetDefinition, SOLAR_SYSTEM_PLANETS


class OrbitalSimulation:
    def __init__(self) -> None:
        self.bodies = self._default_bodies()

    def update(self, dt: float) -> None:
        for body in self.bodies:
            body.angle += body.angular_speed * dt

    def reset(self) -> None:
        self.bodies = self._default_bodies()

    def _default_bodies(self) -> list[CelestialBody]:
        starting_angles = (4.6, 5.25, 1.2, 2.35, 0.48, 3.35, 1.9, 5.65)
        return [
            self._create_body(definition, index, starting_angles[index])
            for index, definition in enumerate(SOLAR_SYSTEM_PLANETS)
        ]

    def _create_body(self, definition: PlanetDefinition, index: int, starting_angle: float) -> CelestialBody:
        return CelestialBody(
            name=definition.name,
            angular_speed=self._angular_speed_for_period(definition.orbital_period_days),
            color=definition.color,
            accent_color=definition.accent_color,
            angle=starting_angle,
            starting_angle=starting_angle,
            radius_km=definition.radius_km,
            distance_au=definition.distance_au,
            orbital_period_days=definition.orbital_period_days,
            fact=definition.fact,
            has_rings=definition.has_rings,
        )

    def _angular_speed_for_period(self, orbital_period_days: float) -> float:
        relative_years = orbital_period_days / 365.25
        animated_period_seconds = 22.0 * (relative_years ** 0.58)
        return tau / animated_period_seconds
