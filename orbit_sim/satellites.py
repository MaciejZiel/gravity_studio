from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MoonDefinition:
    name: str
    parent_name: str
    radius_km: float
    orbital_distance_km: float
    orbital_period_days: float
    inclination_deg: float
    color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    fact: str


MAJOR_MOONS: list[MoonDefinition] = [
    MoonDefinition(
        name="Moon",
        parent_name="Earth",
        radius_km=1737.4,
        orbital_distance_km=384400.0,
        orbital_period_days=27.3,
        inclination_deg=5.1,
        color=(184, 186, 190),
        accent_color=(228, 228, 232),
        fact="Earth's Moon stabilizes the planet's axial tilt and drives the tides.",
    ),
    MoonDefinition(
        name="Io",
        parent_name="Jupiter",
        radius_km=1821.6,
        orbital_distance_km=421700.0,
        orbital_period_days=1.8,
        inclination_deg=0.04,
        color=(216, 196, 112),
        accent_color=(244, 230, 168),
        fact="Io is the most volcanically active world known in the Solar System.",
    ),
    MoonDefinition(
        name="Europa",
        parent_name="Jupiter",
        radius_km=1560.8,
        orbital_distance_km=671100.0,
        orbital_period_days=3.6,
        inclination_deg=0.47,
        color=(198, 186, 174),
        accent_color=(230, 224, 214),
        fact="Europa likely hides a global salty ocean beneath its icy shell.",
    ),
    MoonDefinition(
        name="Ganymede",
        parent_name="Jupiter",
        radius_km=2634.1,
        orbital_distance_km=1070400.0,
        orbital_period_days=7.2,
        inclination_deg=0.2,
        color=(156, 144, 132),
        accent_color=(206, 194, 180),
        fact="Ganymede is the largest moon in the Solar System and has its own magnetic field.",
    ),
    MoonDefinition(
        name="Callisto",
        parent_name="Jupiter",
        radius_km=2410.3,
        orbital_distance_km=1882700.0,
        orbital_period_days=16.7,
        inclination_deg=0.28,
        color=(120, 114, 108),
        accent_color=(184, 178, 170),
        fact="Callisto preserves one of the oldest and most cratered surfaces in the Solar System.",
    ),
    MoonDefinition(
        name="Titan",
        parent_name="Saturn",
        radius_km=2574.7,
        orbital_distance_km=1221870.0,
        orbital_period_days=15.9,
        inclination_deg=0.35,
        color=(198, 168, 124),
        accent_color=(232, 214, 174),
        fact="Titan has a thick nitrogen atmosphere and lakes of liquid methane and ethane.",
    ),
]
