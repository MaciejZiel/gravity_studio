from __future__ import annotations

from math import cos, pi, radians, sin

import pytest

from orbit_sim.models import CelestialBody, MoonBody


def make_body(**overrides) -> CelestialBody:
    values = {
        "name": "Test",
        "angular_speed": 0.1,
        "rotation_hours": 24.0,
        "eccentricity": 0.0,
        "inclination_deg": 0.0,
        "ascending_node_deg": 0.0,
        "periapsis_deg": 0.0,
        "axial_tilt_deg": 0.0,
        "season_offset_deg": 0.0,
        "color": (1, 2, 3),
        "accent_color": (4, 5, 6),
        "angle": 0.0,
        "starting_angle": 0.0,
        "radius_km": 1000.0,
        "distance_au": 2.0,
        "orbital_period_days": 100.0,
        "fact": "",
    }
    values.update(overrides)
    return CelestialBody(**values)


def make_moon(**overrides) -> MoonBody:
    values = {
        "name": "TestMoon",
        "parent_name": "Test",
        "angular_speed": 0.2,
        "angle": 0.0,
        "starting_angle": 0.0,
        "radius_km": 100.0,
        "orbital_distance_km": 1000.0,
        "orbital_period_days": 10.0,
        "inclination_deg": 0.0,
        "color": (1, 2, 3),
        "accent_color": (4, 5, 6),
        "fact": "",
    }
    values.update(overrides)
    return MoonBody(**values)


@pytest.mark.parametrize("angle", [0.0, 0.7, pi / 2, pi, 4.0, 2 * pi - 0.1])
def test_circular_flat_orbit_keeps_constant_radius_in_the_plane(angle):
    position = make_body(distance_au=2.0).orbital_position(angle)
    assert position.length() == pytest.approx(2.0)
    assert position.z == pytest.approx(0.0, abs=1e-12)
    assert position.x == pytest.approx(2.0 * cos(angle))
    assert position.y == pytest.approx(2.0 * sin(angle))


def test_eccentric_orbit_hits_perihelion_and_aphelion_distances():
    body = make_body(distance_au=10.0, eccentricity=0.2, periapsis_deg=40.0)
    periapsis = radians(40.0)
    assert body.orbital_position(periapsis).length() == pytest.approx(10.0 * (1 - 0.2))
    assert body.orbital_position(periapsis + pi).length() == pytest.approx(10.0 * (1 + 0.2))


def test_eccentric_orbit_distance_stays_between_the_two_extremes():
    body = make_body(distance_au=10.0, eccentricity=0.2, periapsis_deg=40.0)
    for step in range(72):
        radius = body.orbital_position(step * radians(5.0)).length()
        assert 10.0 * 0.8 - 1e-9 <= radius <= 10.0 * 1.2 + 1e-9


def test_ascending_node_rotates_a_flat_orbit_about_the_pole():
    node = 30.0
    body = make_body(distance_au=3.0, ascending_node_deg=node)
    position = body.orbital_position(0.5)
    assert position.x == pytest.approx(3.0 * cos(0.5 + radians(node)))
    assert position.y == pytest.approx(3.0 * sin(0.5 + radians(node)))
    assert position.z == pytest.approx(0.0, abs=1e-12)


def test_inclination_lifts_the_body_out_of_the_plane_at_quarter_orbit():
    body = make_body(distance_au=4.0, inclination_deg=30.0)
    position = body.orbital_position(pi / 2)
    assert position.z == pytest.approx(4.0 * sin(radians(30.0)))
    assert position.y == pytest.approx(4.0 * cos(radians(30.0)))
    assert position.x == pytest.approx(0.0, abs=1e-12)
    # Inclination only tilts the orbit, it must not change the distance from the Sun.
    assert position.length() == pytest.approx(4.0)


def test_inclined_orbit_crosses_the_plane_at_the_nodes():
    body = make_body(distance_au=4.0, inclination_deg=30.0)
    assert body.orbital_position(0.0).z == pytest.approx(0.0, abs=1e-12)
    assert body.orbital_position(pi).z == pytest.approx(0.0, abs=1e-12)


def test_orbital_position_defaults_to_the_current_angle():
    body = make_body(angle=1.1)
    assert body.orbital_position() == body.orbital_position(1.1)


def test_orbital_position_has_a_full_turn_period():
    body = make_body(eccentricity=0.1, inclination_deg=5.0, ascending_node_deg=20.0, periapsis_deg=10.0)
    first = body.orbital_position(0.9)
    second = body.orbital_position(0.9 + 2 * pi)
    assert first.x == pytest.approx(second.x)
    assert first.y == pytest.approx(second.y)
    assert first.z == pytest.approx(second.z)


def test_direction_is_a_unit_vector_at_the_current_angle():
    body = make_body(angle=0.8)
    direction = body.direction()
    assert direction.length() == pytest.approx(1.0)
    assert direction.x == pytest.approx(cos(0.8))
    assert direction.y == pytest.approx(sin(0.8))


def test_body_reset_restores_the_starting_angle():
    body = make_body(angle=3.0, starting_angle=0.25)
    body.reset()
    assert body.angle == 0.25


@pytest.mark.parametrize("angle", [0.0, 1.0, pi, 5.5])
def test_flat_moon_offset_is_on_the_unit_circle(angle):
    offset = make_moon(inclination_deg=0.0).orbital_offset(angle)
    assert offset.x == pytest.approx(cos(angle))
    assert offset.y == pytest.approx(sin(angle))


def test_moon_offset_squashes_the_vertical_axis_by_the_inclination():
    offset = make_moon(inclination_deg=60.0).orbital_offset(pi / 2)
    assert offset.y == pytest.approx(0.5)  # cos(60 deg)


def test_moon_vertical_squash_never_collapses_below_the_floor():
    offset = make_moon(inclination_deg=85.0).orbital_offset(pi / 2)
    assert offset.y == pytest.approx(0.34)


def test_moon_reset_restores_the_starting_angle():
    moon = make_moon(angle=2.0, starting_angle=-0.5)
    moon.reset()
    assert moon.angle == -0.5
