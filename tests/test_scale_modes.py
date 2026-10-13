from __future__ import annotations

from math import log1p

import pytest

from orbit_sim.camera import (
    MAX_SOLAR_DISTANCE_AU,
    SCENE_PRESETS,
    STORY_COMPRESSION,
    SolarCamera,
)
from orbit_sim.simulation import OrbitalSimulation

VIEWPORT = (1600, 900)


@pytest.fixture
def camera() -> SolarCamera:
    return SolarCamera(VIEWPORT)


def settle(camera: SolarCamera, steps: int = 400) -> None:
    for _ in range(steps):
        camera.update(0.1, 0.0)


def test_scale_mode_toggles_between_the_two_modes(camera):
    assert camera.scale_mode == "compressed"
    camera.toggle_scale_mode()
    assert camera.scale_mode == "expanded"
    camera.toggle_scale_mode()
    assert camera.scale_mode == "compressed"


def test_expanded_mode_lowers_target_compression_to_62_percent(camera):
    settle(camera)
    compressed = camera.target_compression
    camera.toggle_scale_mode()
    settle(camera)
    assert compressed == pytest.approx(SCENE_PRESETS["full_system"].compression)
    assert camera.target_compression == pytest.approx(compressed * 0.62)


def test_expanded_mode_widens_the_orbit_span_by_two_percent(camera):
    settle(camera)
    base = camera.target_span_factor
    camera.toggle_scale_mode()
    settle(camera)
    assert camera.target_span_factor == pytest.approx(base * 1.02)


def test_scale_story_converges_to_the_story_compression(camera):
    camera.set_scale_story(True)
    settle(camera)
    assert camera.story_progress == pytest.approx(1.0, abs=1e-3)
    assert camera.current_compression == pytest.approx(STORY_COMPRESSION, abs=1e-3)
    camera.set_scale_story(False)
    settle(camera)
    assert camera.current_compression == pytest.approx(SCENE_PRESETS["full_system"].compression, abs=1e-3)


def test_orbit_radius_grows_with_distance(camera):
    simulation = OrbitalSimulation()
    radii = [camera.orbit_radius(body) for body in simulation.bodies]
    assert radii == sorted(radii)
    assert len(set(radii)) == len(radii)


def test_farthest_planet_fills_the_full_orbit_span(camera):
    # At the reference distance the normalised log scale reaches exactly 1.
    radius = camera._orbit_radius_for_distance(MAX_SOLAR_DISTANCE_AU, 1.0, 2.0, 1.0)
    layout = camera.layout
    assert radius == pytest.approx(layout.inner_orbit_radius + layout.orbit_span)


def test_distance_scale_is_logarithmic_not_linear(camera):
    layout = camera.layout
    compression = 2.15
    for distance in (0.39, 1.0, 5.2, 30.05):
        expected_fraction = log1p(distance * compression) / log1p(MAX_SOLAR_DISTANCE_AU * compression)
        expected = layout.inner_orbit_radius + expected_fraction * layout.orbit_span
        assert camera._orbit_radius_for_distance(distance, 1.0, compression, 1.0) == pytest.approx(expected)


def test_neptune_is_far_less_than_77_times_mercury_on_screen(camera):
    inner = camera._orbit_radius_for_distance(0.39, 1.0, 2.15, 1.0)
    neptune = camera._orbit_radius_for_distance(30.05, 1.0, 2.15, 1.0)
    assert 30.05 / 0.39 == pytest.approx(77.05, abs=0.01)
    assert neptune / inner == pytest.approx(4.69, abs=0.01)


def test_lower_compression_spreads_the_inner_system_less(camera):
    heavy = camera._orbit_radius_for_distance(1.0, 1.0, 5.3, 1.0)
    light = camera._orbit_radius_for_distance(1.0, 1.0, 0.5, 1.0)
    assert heavy > light


def test_orbit_radius_scales_with_zoom(camera):
    single = camera._orbit_radius_for_distance(5.2, 1.0, 2.0, 1.0)
    double = camera._orbit_radius_for_distance(5.2, 2.0, 2.0, 1.0)
    assert double == pytest.approx(2 * single)


def test_zoom_is_clamped(camera):
    camera.adjust_zoom(50.0)
    assert camera.target_user_zoom == 2.45
    camera.adjust_zoom(-500.0)
    assert camera.target_user_zoom == 0.72


def test_unknown_scene_is_ignored_and_focus_needs_a_body(camera):
    camera.set_scene("nonexistent")
    assert camera.scene_mode == "full_system"
    camera.set_scene("focus")
    assert camera.scene_mode == "full_system"
    camera.set_scene("inner_worlds")
    assert camera.scene_mode == "inner_worlds"


def test_focusing_a_body_switches_scene_and_clearing_returns_to_system(camera):
    earth = OrbitalSimulation().body_named("Earth")
    camera.set_focus_body(earth)
    assert camera.scene_mode == "focus"
    assert camera.focus_body is earth
    camera.set_scene("gas_giants")
    assert camera.focus_body is None
    camera.set_focus_body(None)
    assert camera.scene_mode == "full_system"


def test_ui_scale_is_clamped_for_extreme_viewports():
    assert SolarCamera((800, 100)).layout.ui_scale == 0.74
    assert SolarCamera((8000, 6000)).layout.ui_scale == 1.55


def test_set_viewport_rebuilds_the_layout(camera):
    camera.set_viewport((1000, 700))
    assert camera.layout.viewport == (1000, 700)
    assert camera.current_center.x == pytest.approx(1000 * SCENE_PRESETS["full_system"].center_ratio[0])


def test_projected_orbit_is_a_closed_loop(camera):
    earth = OrbitalSimulation().body_named("Earth")
    points = camera.project_orbit_points(earth, steps=60)
    assert len(points) == 61
    assert (points[0] - points[-1]).length() < 1e-6
