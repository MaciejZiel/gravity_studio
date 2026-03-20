from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import radians

from orbit_sim.models import CelestialBody
from orbit_sim.solar_system import PlanetDefinition, SOLAR_SYSTEM_PLANETS


SIMULATION_EPOCH = datetime(2000, 1, 1, 12, 0, 0)
TIMELINE_START = datetime(1960, 1, 1, 0, 0, 0)
TIMELINE_END = datetime(2165, 1, 1, 0, 0, 0)
BASE_DAYS_PER_SECOND = 1.2
TIME_SPEED_LEVELS = (1, 10, 100, 1000)


@dataclass(frozen=True)
class TimelineBookmark:
    action: str
    label: str
    moment: datetime


class OrbitalSimulation:
    def __init__(self) -> None:
        self.epoch = SIMULATION_EPOCH
        self.timeline_start_days = (TIMELINE_START - self.epoch).total_seconds() / 86400.0
        self.timeline_end_days = (TIMELINE_END - self.epoch).total_seconds() / 86400.0
        self.timeline_range_days = self.timeline_end_days - self.timeline_start_days
        self.time_speed_levels = TIME_SPEED_LEVELS
        self.time_speed_index = 1
        self.base_days_per_second = BASE_DAYS_PER_SECOND
        self.simulation_days = 0.0
        self.live_mode = False
        self.bodies = self._default_bodies()
        self._sync_body_angles()

    def update(self, dt: float) -> None:
        if self.live_mode:
            self.sync_to_datetime(datetime.now())
        else:
            self.advance_days(dt * self.days_per_second)

    def reset(self) -> None:
        self.simulation_days = 0.0
        self.live_mode = False
        self.bodies = self._default_bodies()
        self._sync_body_angles()

    @property
    def days_per_second(self) -> float:
        return self.base_days_per_second * self.time_speed_levels[self.time_speed_index]

    @property
    def time_speed_label(self) -> str:
        if self.live_mode:
            return "1:1 LIVE"
        return f"{self.time_speed_levels[self.time_speed_index]}x"

    def set_time_speed_index(self, index: int) -> None:
        self.live_mode = False
        self.time_speed_index = max(0, min(index, len(self.time_speed_levels) - 1))

    def set_simulation_days(self, days: float) -> None:
        self.live_mode = False
        self.simulation_days = max(self.timeline_start_days, min(days, self.timeline_end_days))
        self._sync_body_angles()

    def advance_days(self, days: float) -> None:
        advanced_days = self.simulation_days + days
        if advanced_days > self.timeline_end_days:
            advanced_days = self.timeline_start_days + (advanced_days - self.timeline_end_days)
        elif advanced_days < self.timeline_start_days:
            advanced_days = self.timeline_end_days - (self.timeline_start_days - advanced_days)
        self.simulation_days = advanced_days
        self._sync_body_angles()

    def set_live_mode(self, enabled: bool) -> None:
        self.live_mode = enabled
        if enabled:
            self.sync_to_datetime(datetime.now())

    def sync_to_datetime(self, moment: datetime) -> None:
        offset = moment - self.epoch
        self.simulation_days = max(
            self.timeline_start_days,
            min(offset.total_seconds() / 86400.0, self.timeline_end_days),
        )
        self._sync_body_angles()

    @property
    def timeline_progress(self) -> float:
        return (self.simulation_days - self.timeline_start_days) / max(1.0, self.timeline_range_days)

    def set_timeline_progress(self, progress: float) -> None:
        clamped = max(0.0, min(1.0, progress))
        self.set_simulation_days(self.timeline_start_days + self.timeline_range_days * clamped)

    def current_date(self) -> date:
        return self.current_datetime().date()

    def current_datetime(self) -> datetime:
        return self.epoch + timedelta(days=self.simulation_days)

    def bookmarks(self) -> list[TimelineBookmark]:
        current_year = self.current_datetime().year
        return [
            TimelineBookmark("jump_now", "Now", datetime.now().replace(microsecond=0)),
            TimelineBookmark("jump_equinox", "Equinox", datetime(current_year, 3, 20, 12, 0, 0)),
            TimelineBookmark("jump_solstice", "Solstice", datetime(current_year, 6, 21, 12, 0, 0)),
            TimelineBookmark("jump_apollo", "Apollo 11", datetime(1969, 7, 20, 20, 17, 0)),
            TimelineBookmark("jump_voyager", "Voyager 1", datetime(1977, 9, 5, 12, 56, 0)),
        ]

    def jump_to_bookmark(self, action: str) -> None:
        for bookmark in self.bookmarks():
            if bookmark.action == action:
                self.live_mode = action == "jump_now"
                self.sync_to_datetime(bookmark.moment)
                return

    def _default_bodies(self) -> list[CelestialBody]:
        return [self._create_body(definition) for definition in SOLAR_SYSTEM_PLANETS]

    def _create_body(self, definition: PlanetDefinition) -> CelestialBody:
        starting_angle = -radians(definition.mean_longitude_deg)
        return CelestialBody(
            name=definition.name,
            angular_speed=-radians(definition.mean_motion_deg_per_day),
            rotation_hours=definition.rotation_hours,
            eccentricity=definition.eccentricity,
            inclination_deg=definition.inclination_deg,
            ascending_node_deg=definition.ascending_node_deg,
            periapsis_deg=definition.periapsis_deg,
            axial_tilt_deg=definition.axial_tilt_deg,
            season_offset_deg=definition.season_offset_deg,
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

    def _sync_body_angles(self) -> None:
        for body in self.bodies:
            body.angle = body.starting_angle + body.angular_speed * self.simulation_days
