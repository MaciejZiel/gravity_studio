from __future__ import annotations

import os

# Must be set before pygame is imported anywhere so the suite runs without a display or audio device.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from orbit_sim.simulation import OrbitalSimulation


@pytest.fixture
def simulation() -> OrbitalSimulation:
    return OrbitalSimulation()
