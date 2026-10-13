from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import atan2, radians, tau

from orbit_sim.models import CelestialBody, MoonBody
from orbit_sim.satellites import MAJOR_MOONS, MoonDefinition
from orbit_sim.solar_system import SOLAR_SYSTEM_PLANETS, PlanetDefinition

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
    description: str = ""
    featured_body: str | None = None


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
        self.moons = self._default_moons()
        self._alignment_cache_anchor: date | None = None
        self._alignment_cache: TimelineBookmark | None = None
        self._bookmark_cache_key: tuple[date, int] | None = None
        self._bookmark_cache_rest: tuple[TimelineBookmark, ...] = ()
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
        self.moons = self._default_moons()
        self._alignment_cache_anchor = None
        self._alignment_cache = None
        self._bookmark_cache_key = None
        self._bookmark_cache_rest = ()
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

    def bookmarks(self, moment: datetime | None = None) -> list[TimelineBookmark]:
        current_moment = self.current_datetime() if moment is None else moment
        cache_key = (current_moment.date(), current_moment.year)
        if self._bookmark_cache_key != cache_key:
            current_year = current_moment.year
            next_alignment = self._next_alignment_bookmark(current_moment.date())
            self._bookmark_cache_key = cache_key
            self._bookmark_cache_rest = (
                next_alignment,
                TimelineBookmark("jump_equinox", "Equinox", datetime(current_year, 3, 20, 12, 0, 0), "Solar illumination crosses Earth's equator evenly.", "Earth"),
                TimelineBookmark("jump_solstice", "Solstice", datetime(current_year, 6, 21, 12, 0, 0), "Earth's axial tilt is at a seasonal extreme.", "Earth"),
                TimelineBookmark("jump_eclipse", "Eclipse Season", datetime(2024, 4, 8, 18, 18, 0), "The Sun, Moon and Earth line up for the 2024 total solar eclipse.", "Earth"),
                TimelineBookmark("jump_apollo", "Apollo 11", datetime(1969, 7, 20, 20, 17, 0), "Apollo 11 lands in the Sea of Tranquility.", "Earth"),
                TimelineBookmark("jump_voyager", "Voyager 1", datetime(1977, 9, 5, 12, 56, 0), "Voyager 1 begins its outward grand tour.", "Jupiter"),
                TimelineBookmark("jump_webb", "JWST", datetime(2022, 1, 24, 19, 0, 0), "James Webb settles near the Earth-Sun L2 point.", "Earth"),
            )
        return [
            TimelineBookmark("jump_now", "Now", datetime.now().replace(microsecond=0), "Match the current live heliocentric arrangement."),
            *self._bookmark_cache_rest,
        ]

    def jump_to_bookmark(self, action: str) -> None:
        if action == "jump_now":
            self.live_mode = True
            self.sync_to_datetime(datetime.now())
            return
        for bookmark in self.bookmarks():
            if bookmark.action == action:
                self.live_mode = action == "jump_now"
                self.sync_to_datetime(bookmark.moment)
                return

    def _default_bodies(self) -> list[CelestialBody]:
        return [self._create_body(definition) for definition in SOLAR_SYSTEM_PLANETS]

    def _default_moons(self) -> list[MoonBody]:
        return [self._create_moon(definition) for definition in MAJOR_MOONS]

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

    def _create_moon(self, definition: MoonDefinition) -> MoonBody:
        starting_angle = -radians((len(definition.name) * 37) % 360)
        return MoonBody(
            name=definition.name,
            parent_name=definition.parent_name,
            angular_speed=tau / definition.orbital_period_days,
            angle=starting_angle,
            starting_angle=starting_angle,
            radius_km=definition.radius_km,
            orbital_distance_km=definition.orbital_distance_km,
            orbital_period_days=definition.orbital_period_days,
            inclination_deg=definition.inclination_deg,
            color=definition.color,
            accent_color=definition.accent_color,
            fact=definition.fact,
        )

    def body_named(self, name: str) -> CelestialBody | None:
        for body in self.bodies:
            if body.name == name:
                return body
        return None

    def moons_for(self, parent_name: str) -> list[MoonBody]:
        return [moon for moon in self.moons if moon.parent_name == parent_name]

    def _sync_body_angles(self) -> None:
        for body in self.bodies:
            body.angle = body.starting_angle + body.angular_speed * self.simulation_days
        for moon in self.moons:
            moon.angle = moon.starting_angle + moon.angular_speed * self.simulation_days

    def _next_alignment_bookmark(self, anchor_date: date | None = None) -> TimelineBookmark:
        anchor_date = self.current_datetime().date() if anchor_date is None else anchor_date
        if self._alignment_cache_anchor == anchor_date and self._alignment_cache is not None:
            return self._alignment_cache

        anchor_moment = datetime.combine(anchor_date, datetime.min.time())
        best_moment = anchor_moment
        best_span = 360.0
        for day_offset in range(1, 731, 2):
            candidate = anchor_moment + timedelta(days=day_offset)
            longitudes = self._alignment_longitudes(candidate)
            span = max(longitudes) - min(longitudes)
            if span > 180.0:
                wrapped = sorted(longitudes)
                largest_gap = max(
                    (wrapped[(index + 1) % len(wrapped)] - wrapped[index]) % 360.0
                    for index in range(len(wrapped))
                )
                span = 360.0 - largest_gap
            if span < best_span:
                best_span = span
                best_moment = candidate

        self._alignment_cache_anchor = anchor_date
        self._alignment_cache = TimelineBookmark(
            "jump_alignment",
            "Next Alignment",
            best_moment.replace(hour=12),
            "A compact grouping of the bright planets in Earth's sky.",
            "Venus",
        )
        return self._alignment_cache

    def _alignment_longitudes(self, moment: datetime) -> list[float]:
        days = (moment - self.epoch).total_seconds() / 86400.0
        earth = self._body_position_at(self.body_named("Earth"), days)
        targets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        longitudes = []
        for name in targets:
            body = self.body_named(name)
            vector = self._body_position_at(body, days) - earth
            longitudes.append((atan2(vector.y, vector.x) * 180.0 / 3.141592653589793 + 360.0) % 360.0)
        return longitudes

    def _body_position_at(self, body: CelestialBody | None, simulation_days: float):
        if body is None:
            return type(self.bodies[0].orbital_position())()
        return body.orbital_position(body.starting_angle + body.angular_speed * simulation_days)
