from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MissionDefinition:
    name: str
    label: str
    frame: str
    launch: datetime
    progress_end: datetime
    color: tuple[int, int, int]
    path_points: tuple[tuple[float, float], ...]
    description: str


MISSION_DEFINITIONS: list[MissionDefinition] = [
    MissionDefinition(
        name="Parker Solar Probe",
        label="Parker",
        frame="heliocentric",
        launch=datetime(2018, 8, 12, 7, 31, 0),
        progress_end=datetime(2026, 12, 31, 0, 0, 0),
        color=(228, 174, 102),
        path_points=((0.72, 0.0), (0.52, -0.22), (0.28, -0.08), (0.18, 0.06), (0.11, 0.0)),
        description="Parker Solar Probe repeatedly dives into the Sun's corona.",
    ),
    MissionDefinition(
        name="JWST",
        label="JWST",
        frame="heliocentric",
        launch=datetime(2021, 12, 25, 12, 20, 0),
        progress_end=datetime(2022, 2, 1, 0, 0, 0),
        color=(182, 214, 244),
        path_points=((1.0, 0.0), (1.01, -0.02), (1.018, 0.01), (1.022, 0.0)),
        description="The James Webb Space Telescope sits near the Sun-Earth L2 point.",
    ),
    MissionDefinition(
        name="Voyager 1",
        label="Voyager 1",
        frame="heliocentric",
        launch=datetime(1977, 9, 5, 12, 56, 0),
        progress_end=datetime(1990, 2, 14, 0, 0, 0),
        color=(170, 204, 244),
        path_points=((1.0, 0.0), (2.1, 0.34), (5.2, 1.0), (9.6, 0.6), (18.0, -1.1), (30.0, -2.0)),
        description="Voyager 1 used Jupiter and Saturn gravity assists to leave the planetary plane.",
    ),
    MissionDefinition(
        name="Cassini-Huygens",
        label="Cassini",
        frame="heliocentric",
        launch=datetime(1997, 10, 15, 8, 43, 0),
        progress_end=datetime(2004, 7, 1, 0, 0, 0),
        color=(214, 196, 152),
        path_points=((1.0, 0.0), (0.72, -0.28), (0.95, 0.18), (5.2, 0.92), (9.58, 0.44)),
        description="Cassini reached Saturn after a complex sequence of inner-planet flybys.",
    ),
    MissionDefinition(
        name="Apollo 11",
        label="Apollo 11",
        frame="earth_local",
        launch=datetime(1969, 7, 16, 13, 32, 0),
        progress_end=datetime(1969, 7, 24, 16, 50, 0),
        color=(228, 228, 236),
        path_points=((0.0, 0.0), (0.18, -0.12), (0.48, 0.0), (0.28, 0.16), (0.0, 0.0)),
        description="Apollo 11 carried humans from low Earth orbit to the lunar surface and back.",
    ),
]
