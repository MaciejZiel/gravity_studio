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


@pytest.mark.parametrize("payload", ["[]", "[1, 2, 3]", '"text"', "42", "null", "true"])
def test_valid_json_that_is_not_an_object_returns_defaults(tmp_path, payload):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text(payload)
    assert store.load() == StudioSettings()


@pytest.mark.parametrize("stored", ["loud", None, [], {}, "", "NaN"])
def test_unusable_master_volume_falls_back_to_the_default(tmp_path, stored):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text(json.dumps({"master_volume": stored, "show_orbits": False}))
    loaded = store.load()
    assert loaded.master_volume == StudioSettings().master_volume
    # The rest of the file is still honoured.
    assert loaded.show_orbits is False


def test_nan_master_volume_falls_back_to_the_default(tmp_path):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text('{"master_volume": NaN}')
    assert store.load().master_volume == StudioSettings().master_volume


def test_non_utf8_file_returns_defaults(tmp_path):
    store = StudioSettingsStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_bytes(b"\xff\xfe\x00garbage")
    assert store.load() == StudioSettings()


def test_unreadable_settings_path_returns_defaults(tmp_path):
    store = StudioSettingsStore(tmp_path)
    store.path.mkdir(parents=True)  # a directory where the file should be
    assert store.load() == StudioSettings()


def write_settings(store, text):
    store.path.parent.mkdir(parents=True)
    store.path.write_text(text)


def test_huge_integer_master_volume_falls_back_instead_of_crashing(tmp_path):
    store = StudioSettingsStore(tmp_path)
    write_settings(store, '{"master_volume": 1' + "0" * 400 + ', "show_orbits": false}')
    loaded = store.load()
    assert loaded.master_volume == StudioSettings().master_volume
    assert loaded.show_orbits is False


@pytest.mark.parametrize(
    ("stored", "expected"),
    [("false", False), ("False", False), ("0", False), ("off", False), ("no", False),
     ("true", True), ("TRUE", True), ("1", True), ("on", True), (0, False), (1, True)],
)
def test_booleans_are_parsed_not_just_truthy(tmp_path, stored, expected):
    store = StudioSettingsStore(tmp_path)
    write_settings(store, json.dumps({"show_orbits": stored, "ui_hidden": stored}))
    loaded = store.load()
    assert loaded.show_orbits is expected
    assert loaded.ui_hidden is expected


@pytest.mark.parametrize("stored", ["maybe", "", 2, -1, 0.5, None, [], {}, [False]])
def test_unusable_booleans_fall_back_to_each_default(tmp_path, stored):
    store = StudioSettingsStore(tmp_path)
    write_settings(store, json.dumps({"show_orbits": stored, "ui_hidden": stored}))
    loaded = store.load()
    assert loaded.show_orbits is True  # default True
    assert loaded.ui_hidden is False  # default False

