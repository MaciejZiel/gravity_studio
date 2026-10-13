from __future__ import annotations

import json

import pytest

from orbit_sim.settings import StudioSettings, StudioSettingsStore


def test_missing_file_returns_defaults(tmp_path):
    assert StudioSettingsStore(tmp_path).load() == StudioSettings()


def test_save_then_load_round_trips(tmp_path):
    store = StudioSettingsStore(tmp_path)
    settings = StudioSettings(show_orbits=False, scale_mode="expanded", last_scene="focus", ui_hidden=True, master_volume=0.8)
    store.save(settings)
    assert store.path == tmp_path / ".gravity_studio" / "settings.json"
    assert store.load() == settings


def test_save_creates_the_settings_directory(tmp_path):
    root = tmp_path / "nested"
    StudioSettingsStore(root).save(StudioSettings())
    assert (root / ".gravity_studio" / "settings.json").is_file()


def test_invalid_json_returns_defaults(tmp_path):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text("{not json")
    assert store.load() == StudioSettings()


def test_partial_file_fills_missing_keys_with_defaults(tmp_path):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text(json.dumps({"show_labels": False}))
    loaded = store.load()
    assert loaded.show_labels is False
    assert loaded == StudioSettings(show_labels=False)


@pytest.mark.parametrize(("stored", "expected"), [(5, 1.0), (-2, 0.0), (0.25, 0.25), ("0.6", 0.6)])
def test_master_volume_is_clamped_to_the_unit_range(tmp_path, stored, expected):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text(json.dumps({"master_volume": stored}))
    assert store.load().master_volume == pytest.approx(expected)
