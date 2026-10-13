from __future__ import annotations

from datetime import datetime, timedelta
from math import radians

import pytest

from orbit_sim.simulation import (
    BASE_DAYS_PER_SECOND,
    SIMULATION_EPOCH,
    TIME_SPEED_LEVELS,
    TIMELINE_START,
    OrbitalSimulation,
)

ONE_SECOND = timedelta(seconds=1)


def test_starts_at_the_epoch_and_paused_from_live_mode(simulation):
    assert simulation.simulation_days == 0.0
    assert simulation.current_datetime() == SIMULATION_EPOCH == datetime(2000, 1, 1, 12, 0, 0)
    assert simulation.live_mode is False


def test_timeline_bounds_in_days_match_the_calendar(simulation):
    assert simulation.timeline_start_days == pytest.approx((TIMELINE_START - SIMULATION_EPOCH).days + (TIMELINE_START - SIMULATION_EPOCH).seconds / 86400)
    assert simulation.timeline_start_days < 0 < simulation.timeline_end_days
    assert simulation.timeline_range_days == pytest.approx(simulation.timeline_end_days - simulation.timeline_start_days)
    # 1960-01-01 to 2165-01-01 is 205 calendar years.
    assert simulation.timeline_range_days / 365.2425 == pytest.approx(205, abs=0.1)


def test_set_simulation_days_updates_the_calendar(simulation):
    simulation.set_simulation_days(366.0)
    assert simulation.current_datetime() == datetime(2001, 1, 1, 12, 0, 0)
    assert simulation.current_date() == datetime(2001, 1, 1).date()


def test_set_simulation_days_clamps_to_the_timeline(simulation):
    simulation.set_simulation_days(1e9)
    assert simulation.simulation_days == simulation.timeline_end_days
    simulation.set_simulation_days(-1e9)
    assert simulation.simulation_days == simulation.timeline_start_days


def test_set_simulation_days_leaves_live_mode(simulation):
    simulation.set_live_mode(True)
    simulation.set_simulation_days(10.0)
    assert simulation.live_mode is False


def test_timeline_progress_runs_from_zero_to_one(simulation):
    simulation.set_simulation_days(simulation.timeline_start_days)
    assert simulation.timeline_progress == pytest.approx(0.0)
    simulation.set_simulation_days(simulation.timeline_end_days)
    assert simulation.timeline_progress == pytest.approx(1.0)


def test_set_timeline_progress_maps_linearly_and_clamps(simulation):
    simulation.set_timeline_progress(0.5)
    midpoint = simulation.timeline_start_days + simulation.timeline_range_days / 2
    assert simulation.simulation_days == pytest.approx(midpoint)
    assert simulation.timeline_progress == pytest.approx(0.5)
    simulation.set_timeline_progress(7.0)
    assert simulation.simulation_days == simulation.timeline_end_days
    simulation.set_timeline_progress(-3.0)
    assert simulation.simulation_days == simulation.timeline_start_days


def test_sync_to_datetime_round_trips(simulation):
    moment = datetime(1969, 7, 20, 20, 17, 0)
    simulation.sync_to_datetime(moment)
    assert abs(simulation.current_datetime() - moment) < ONE_SECOND


def test_sync_to_datetime_clamps_outside_the_timeline(simulation):
    simulation.sync_to_datetime(datetime(1900, 1, 1))
    assert simulation.simulation_days == simulation.timeline_start_days
    simulation.sync_to_datetime(datetime(3000, 1, 1))
    assert simulation.simulation_days == simulation.timeline_end_days


def test_advance_days_moves_forward_and_backward(simulation):
    simulation.advance_days(10.5)
    assert simulation.simulation_days == pytest.approx(10.5)
    simulation.advance_days(-20.5)
    assert simulation.simulation_days == pytest.approx(-10.0)


def test_advance_days_wraps_past_the_end_to_the_start(simulation):
    simulation.set_simulation_days(simulation.timeline_end_days - 5.0)
    simulation.advance_days(8.0)
    assert simulation.simulation_days == pytest.approx(simulation.timeline_start_days + 3.0)


def test_advance_days_wraps_past_the_start_to_the_end(simulation):
    simulation.set_simulation_days(simulation.timeline_start_days + 2.0)
    simulation.advance_days(-5.0)
    assert simulation.simulation_days == pytest.approx(simulation.timeline_end_days - 3.0)


def test_speed_levels_and_days_per_second(simulation):
    assert simulation.time_speed_levels == TIME_SPEED_LEVELS == (1, 10, 100, 1000)
    assert simulation.time_speed_index == 1
    assert simulation.days_per_second == pytest.approx(BASE_DAYS_PER_SECOND * 10)
    simulation.set_time_speed_index(3)
    assert simulation.days_per_second == pytest.approx(BASE_DAYS_PER_SECOND * 1000)
    assert simulation.time_speed_label == "1000x"


def test_speed_index_is_clamped_and_leaves_live_mode(simulation):
    simulation.set_live_mode(True)
    simulation.set_time_speed_index(99)
    assert simulation.time_speed_index == 3
    assert simulation.live_mode is False
    simulation.set_time_speed_index(-4)
    assert simulation.time_speed_index == 0


def test_live_mode_label_overrides_the_speed_label(simulation):
    simulation.set_live_mode(True)
    assert simulation.time_speed_label == "1:1 LIVE"


def test_update_advances_by_dt_times_days_per_second(simulation):
    simulation.update(2.0)
    assert simulation.simulation_days == pytest.approx(2.0 * simulation.days_per_second)


def test_update_in_live_mode_tracks_the_wall_clock(simulation):
    simulation.set_live_mode(True)
    simulation.update(5.0)
    assert abs(simulation.current_datetime() - datetime.now()) < timedelta(seconds=5)


def test_reset_restores_the_initial_state(simulation):
    simulation.set_live_mode(True)
    simulation.set_simulation_days(5000.0)
    simulation.reset()
    fresh = OrbitalSimulation()
    assert simulation.simulation_days == 0.0
    assert simulation.live_mode is False
    assert [body.angle for body in simulation.bodies] == [body.angle for body in fresh.bodies]
    assert [moon.angle for moon in simulation.moons] == [moon.angle for moon in fresh.moons]


def test_body_angle_at_epoch_is_minus_the_mean_longitude(simulation):
    earth = simulation.body_named("Earth")
    assert earth.angle == pytest.approx(-radians(100.46457166))
    assert earth.starting_angle == earth.angle


def test_body_angles_advance_linearly_with_time(simulation):
    earth = simulation.body_named("Earth")
    start = earth.angle
    simulation.set_simulation_days(100.0)
    assert earth.angle == pytest.approx(start + earth.angular_speed * 100.0)
    assert earth.angle < start  # the model orbits clockwise (negative angular speed)


def test_earth_completes_one_orbit_in_a_sidereal_year(simulation):
    earth = simulation.body_named("Earth")
    start_position = earth.orbital_position()
    simulation.set_simulation_days(365.25636713)
    end_position = earth.orbital_position()
    assert (end_position - start_position).length() < 1e-3


def test_moon_orbits_with_its_listed_period(simulation):
    moon = simulation.moons_for("Earth")[0]
    start = moon.angle
    simulation.set_simulation_days(moon.orbital_period_days)
    assert moon.angle - start == pytest.approx(2 * 3.141592653589793)


def test_body_lookup_and_moon_grouping(simulation):
    assert simulation.body_named("Mars").name == "Mars"
    assert simulation.body_named("Pluto") is None
    assert [moon.name for moon in simulation.moons_for("Jupiter")] == ["Io", "Europa", "Ganymede", "Callisto"]
    assert simulation.moons_for("Mercury") == []


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("jump_apollo", datetime(1969, 7, 20, 20, 17, 0)),
        ("jump_voyager", datetime(1977, 9, 5, 12, 56, 0)),
        ("jump_webb", datetime(2022, 1, 24, 19, 0, 0)),
        ("jump_eclipse", datetime(2024, 4, 8, 18, 18, 0)),
    ],
)
def test_fixed_date_jumps_land_on_the_documented_moment(simulation, action, expected):
    simulation.jump_to_bookmark(action)
    assert abs(simulation.current_datetime() - expected) < ONE_SECOND
    assert simulation.live_mode is False


def test_equinox_and_solstice_follow_the_current_year(simulation):
    simulation.set_simulation_days((datetime(2031, 5, 1) - SIMULATION_EPOCH).days)
    simulation.jump_to_bookmark("jump_equinox")
    assert abs(simulation.current_datetime() - datetime(2031, 3, 20, 12, 0, 0)) < ONE_SECOND
    simulation.set_simulation_days((datetime(2031, 5, 1) - SIMULATION_EPOCH).days)
    simulation.jump_to_bookmark("jump_solstice")
    assert abs(simulation.current_datetime() - datetime(2031, 6, 21, 12, 0, 0)) < ONE_SECOND


def test_jump_now_enters_live_mode_at_the_current_time(simulation):
    simulation.jump_to_bookmark("jump_now")
    assert simulation.live_mode is True
    assert abs(simulation.current_datetime() - datetime.now()) < timedelta(seconds=5)


def test_unknown_jump_action_changes_nothing(simulation):
    simulation.set_simulation_days(123.0)
    simulation.jump_to_bookmark("jump_nowhere")
    assert simulation.simulation_days == 123.0


def test_next_alignment_is_within_two_years_after_the_current_date(simulation):
    anchor = datetime(2010, 6, 1, 0, 0, 0)
    alignment = next(b for b in simulation.bookmarks(anchor) if b.action == "jump_alignment")
    assert anchor < alignment.moment <= anchor + timedelta(days=731, hours=12)
    assert alignment.moment.hour == 12
    assert alignment.featured_body == "Venus"


def test_next_alignment_is_cached_for_the_same_date(simulation):
    anchor = datetime(2010, 6, 1, 0, 0, 0)
    first = simulation._next_alignment_bookmark(anchor.date())
    assert simulation._next_alignment_bookmark(anchor.date()) is first
