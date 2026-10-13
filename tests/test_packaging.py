from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from orbit_sim.planet_textures import ASSET_DIRECTORY

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pyproject() -> dict:
    tomllib = pytest.importorskip("tomllib")  # standard library from Python 3.11
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def requirement_lines(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def test_requirements_txt_matches_pyproject_dependencies(pyproject):
    assert requirement_lines(ROOT / "requirements.txt") == pyproject["project"]["dependencies"]


def test_console_entry_point_resolves_to_a_callable(pyproject):
    target = pyproject["project"]["scripts"]["gravity-studio"]
    module_name, _, attribute = target.partition(":")
    assert callable(getattr(importlib.import_module(module_name), attribute))


def test_python_floor_matches_the_ci_matrix(pyproject):
    assert pyproject["project"]["requires-python"] == ">=3.10"
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert '"3.10"' in workflow


def test_asset_directory_is_assets_planets_two_levels_above_the_module():
    # The PyInstaller spec ships ./assets as "assets" and the app resolves it with parents[1] from
    # orbit_sim/planet_textures.py, which under _MEIPASS lands on _MEIPASS/assets/planets.
    assert ASSET_DIRECTORY == ROOT / "assets" / "planets"


def test_pyinstaller_spec_bundles_the_assets_directory_to_the_same_relative_path():
    spec = (ROOT / "gravity_studio.spec").read_text(encoding="utf-8")
    assert re.search(r'\(str\(project_root / "assets"\), "assets"\)', spec)
    assert 'project_root = Path(SPECPATH)' in spec
    assert 'name="GravityStudio"' in spec
