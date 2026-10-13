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


def test_python_range_matches_the_ci_matrix(pyproject):
    # pygame 2.6.1 has no cp314 wheel and its sdist does not build, so the upper bound is deliberate.
    assert pyproject["project"]["requires-python"] == ">=3.10,<3.14"
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    versions = re.search(r"python-version: \[(.*?)\]", workflow).group(1)
    assert re.findall(r'"(3\.\d+)"', versions) == ["3.10", "3.11", "3.12", "3.13"]


class _Recorder:
    """Stands in for the PyInstaller spec classes and keeps what the spec passes to them."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.pure = []
        self.scripts = []
        self.binaries = []
        self.datas = kwargs.get("datas", [])


@pytest.fixture(scope="module")
def spec_namespace() -> dict:
    namespace = {"SPECPATH": str(ROOT), "Analysis": _Recorder, "PYZ": _Recorder, "EXE": _Recorder}
    source = (ROOT / "gravity_studio.spec").read_text(encoding="utf-8")
    exec(compile(source, "gravity_studio.spec", "exec"), namespace)
    return namespace


def test_asset_directory_is_derived_from_the_module_location():
    import orbit_sim.planet_textures as module

    assert ASSET_DIRECTORY == Path(module.__file__).resolve().parents[1] / "assets" / "planets"
    assert ASSET_DIRECTORY == ROOT / "assets" / "planets"


def test_pyinstaller_spec_bundles_assets_where_the_module_looks_for_them(spec_namespace):
    ((source, destination),) = spec_namespace["a"].kwargs["datas"]
    assert Path(source) == ROOT / "assets"
    assert Path(source).is_dir()
    # The module finds its textures at <package parent>/assets/planets; in the bundle that parent is the
    # extraction root, so the spec must place the directory at "<destination>" directly under it.
    assert ASSET_DIRECTORY.relative_to(ROOT) == Path(destination) / "planets"


def test_pyinstaller_spec_builds_the_windowed_app_from_main(spec_namespace):
    assert spec_namespace["a"].args == (["main.py"],)
    assert spec_namespace["exe"].kwargs["name"] == "GravityStudio"
    assert spec_namespace["exe"].kwargs["console"] is False
    assert (ROOT / "main.py").is_file()
