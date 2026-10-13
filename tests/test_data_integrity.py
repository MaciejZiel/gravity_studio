from __future__ import annotations

from collections import Counter
from datetime import datetime

import pytest

from orbit_sim.camera import SCENE_PRESETS
from orbit_sim.missions import MISSION_DEFINITIONS
from orbit_sim.planet_assets import PLANET_TEXTURE_SOURCES, SPECIAL_TEXTURE_SOURCES
from orbit_sim.planet_textures import ASSET_DIRECTORY
from orbit_sim.satellites import MAJOR_MOONS
from orbit_sim.simulation import TIMELINE_END, TIMELINE_START, OrbitalSimulation
from orbit_sim.solar_system import SOLAR_SYSTEM_PLANETS
from orbit_sim.tours import TOUR_DEFINITIONS

PLANET_NAMES = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]


def test_planets_are_the_eight_planets_in_distance_order():
    assert [planet.name for planet in SOLAR_SYSTEM_PLANETS] == PLANET_NAMES
    distances = [planet.distance_au for planet in SOLAR_SYSTEM_PLANETS]
    assert distances == sorted(distances)
    assert len(set(distances)) == len(distances)


def test_only_saturn_has_rings():
    assert [planet.name for planet in SOLAR_SYSTEM_PLANETS if planet.has_rings] == ["Saturn"]


@pytest.mark.parametrize("planet", SOLAR_SYSTEM_PLANETS, ids=lambda planet: planet.name)
def test_planet_values_are_physically_plausible(planet):
    assert planet.radius_km > 0
    assert planet.distance_au > 0
    assert planet.orbital_period_days > 0
    assert planet.rotation_hours != 0
    assert 0.0 <= planet.eccentricity < 0.3
    assert 0.0 <= planet.inclination_deg < 10.0
    assert 0.0 <= planet.axial_tilt_deg <= 180.0
    assert planet.mean_motion_deg_per_day > 0
    assert planet.fact.strip()
    for channel in (*planet.color, *planet.accent_color):
        assert 0 <= channel <= 255


@pytest.mark.parametrize("planet", SOLAR_SYSTEM_PLANETS, ids=lambda planet: planet.name)
def test_mean_motion_agrees_with_the_listed_orbital_period(planet):
    period_from_motion = 360.0 / planet.mean_motion_deg_per_day
    assert period_from_motion == pytest.approx(planet.orbital_period_days, rel=0.01)


@pytest.mark.parametrize("planet", SOLAR_SYSTEM_PLANETS, ids=lambda planet: planet.name)
def test_distance_follows_keplers_third_law(planet):
    # T^2 = a^3 with T in years and a in AU; the dataset rounds a to two decimals.
    period_years = planet.orbital_period_days / 365.25
    assert period_years**2 == pytest.approx(planet.distance_au**3, rel=0.03)


def test_retrograde_rotation_is_only_venus_and_uranus():
    retrograde = [planet.name for planet in SOLAR_SYSTEM_PLANETS if planet.rotation_hours < 0]
    assert retrograde == ["Venus", "Uranus"]


def test_moon_names_are_unique_and_do_not_collide_with_planets():
    names = [moon.name for moon in MAJOR_MOONS]
    assert not [name for name, count in Counter(names).items() if count > 1]
    assert not set(names) & set(PLANET_NAMES)


@pytest.mark.parametrize("moon", MAJOR_MOONS, ids=lambda moon: moon.name)
def test_moon_values_are_plausible_and_parent_exists(moon):
    assert moon.parent_name in PLANET_NAMES
    assert moon.radius_km > 0
    assert moon.orbital_distance_km > 0
    assert 0 < moon.orbital_period_days < 100
    assert 0.0 <= moon.inclination_deg < 30.0
    assert moon.fact.strip()


def test_expected_moon_assignment():
    by_parent = Counter(moon.parent_name for moon in MAJOR_MOONS)
    assert by_parent == {"Earth": 1, "Jupiter": 4, "Saturn": 1}


def test_galilean_moons_are_ordered_by_distance_and_period():
    galilean = [moon for moon in MAJOR_MOONS if moon.parent_name == "Jupiter"]
    assert [moon.name for moon in galilean] == ["Io", "Europa", "Ganymede", "Callisto"]
    assert [moon.orbital_distance_km for moon in galilean] == sorted(moon.orbital_distance_km for moon in galilean)
    assert [moon.orbital_period_days for moon in galilean] == sorted(moon.orbital_period_days for moon in galilean)


def test_mission_names_are_unique():
    names = [mission.name for mission in MISSION_DEFINITIONS]
    assert len(set(names)) == len(names)
    assert len({mission.label for mission in MISSION_DEFINITIONS}) == len(names)


@pytest.mark.parametrize("mission", MISSION_DEFINITIONS, ids=lambda mission: mission.name)
def test_mission_dates_and_paths_are_valid(mission):
    assert mission.frame in {"heliocentric", "earth_local"}
    assert mission.launch < mission.progress_end
    assert TIMELINE_START <= mission.launch
    assert mission.progress_end <= TIMELINE_END
    assert len(mission.path_points) >= 2
    assert all(len(point) == 2 for point in mission.path_points)
    assert mission.description.strip()
    assert all(0 <= channel <= 255 for channel in mission.color)


def test_closed_local_mission_returns_to_its_origin():
    apollo = next(mission for mission in MISSION_DEFINITIONS if mission.name == "Apollo 11")
    assert apollo.path_points[0] == apollo.path_points[-1] == (0.0, 0.0)


def test_tour_actions_are_unique_and_have_steps():
    actions = [tour.action for tour in TOUR_DEFINITIONS]
    assert len(set(actions)) == len(actions)
    for tour in TOUR_DEFINITIONS:
        assert tour.steps
        assert len({step.key for step in tour.steps}) == len(tour.steps)


def test_tour_steps_reference_real_scenes_bodies_and_jumps(simulation: OrbitalSimulation):
    jump_actions = {bookmark.action for bookmark in simulation.bookmarks()}
    for tour in TOUR_DEFINITIONS:
        for step in tour.steps:
            assert step.scene_mode in SCENE_PRESETS, (tour.action, step.key)
            assert step.duration > 0
            if step.focus_body is not None:
                assert simulation.body_named(step.focus_body) is not None, (tour.action, step.key)
                assert step.scene_mode == "focus"
            if step.jump_action is not None:
                assert step.jump_action in jump_actions, (tour.action, step.key)


def test_bookmarks_have_unique_actions_and_features_existing_bodies(simulation: OrbitalSimulation):
    bookmarks = simulation.bookmarks()
    actions = [bookmark.action for bookmark in bookmarks]
    assert len(set(actions)) == len(actions)
    assert actions[0] == "jump_now"
    for bookmark in bookmarks:
        if bookmark.featured_body is not None:
            assert simulation.body_named(bookmark.featured_body) is not None, bookmark.action


def test_fixed_date_bookmarks_fall_inside_the_timeline(simulation: OrbitalSimulation):
    for bookmark in simulation.bookmarks(datetime(2000, 1, 1)):
        assert TIMELINE_START <= bookmark.moment <= TIMELINE_END, bookmark.action


def test_every_planet_has_a_texture_source_and_a_file_on_disk():
    assert set(PLANET_TEXTURE_SOURCES) == set(PLANET_NAMES)
    for name, source in PLANET_TEXTURE_SOURCES.items():
        assert source["filename"] == f"{name.lower()}.jpg"
        assert (ASSET_DIRECTORY / source["filename"]).is_file(), source["filename"]


def test_auxiliary_textures_exist_on_disk():
    for key, source in SPECIAL_TEXTURE_SOURCES.items():
        assert source["filename"].startswith(key)
        assert (ASSET_DIRECTORY / source["filename"]).is_file(), source["filename"]
