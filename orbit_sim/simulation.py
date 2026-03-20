from __future__ import annotations

from datetime import date, timedelta
from math import tau

from orbit_sim.models import CelestialBody
from orbit_sim.solar_system import PlanetDefinition, SOLAR_SYSTEM_PLANETS


SIMULATION_EPOCH = date(2000, 1, 1)
TIMELINE_RANGE_DAYS = 365.25 * 165
BASE_DAYS_PER_SECOND = 1.2
TIME_SPEED_LEVELS = (1, 10, 100, 1000)


class OrbitalSimulation:
    def __init__(self) -> None:
        self.epoch = SIMULATION_EPOCH
        self.timeline_range_days = TIMELINE_RANGE_DAYS
        self.time_speed_levels = TIME_SPEED_LEVELS
        self.time_speed_index = 1
        self.base_days_per_second = BASE_DAYS_PER_SECOND
        self.simulation_days = 0.0
        self.bodies = self._default_bodies()
        self._sync_body_angles()

    def update(self, dt: float) -> None:
        self.advance_days(dt * self.days_per_second)

    def reset(self) -> None:
        self.simulation_days = 0.0
        self.bodies = self._default_bodies()
        self._sync_body_angles()

    @property
    def days_per_second(self) -> float:
        return self.base_days_per_second * self.time_speed_levels[self.time_speed_index]

    @property
    def time_speed_label(self) -> str:
        return f"{self.time_speed_levels[self.time_speed_index]}x"

    def set_time_speed_index(self, index: int) -> None:
        self.time_speed_index = max(0, min(index, len(self.time_speed_levels) - 1))

    def set_simulation_days(self, days: float) -> None:
        self.simulation_days = max(0.0, min(days, self.timeline_range_days))
        self._sync_body_angles()

    def advance_days(self, days: float) -> None:
        self.simulation_days = (self.simulation_days + days) % self.timeline_range_days
        self._sync_body_angles()

    def current_date(self) -> date:
        return self.epoch + timedelta(days=self.simulation_days)

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
        return tau / orbital_period_days

    def _sync_body_angles(self) -> None:
        for body in self.bodies:
            body.angle = body.starting_angle + body.angular_speed * self.simulation_days
