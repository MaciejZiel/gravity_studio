from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanetDefinition:
    name: str
    radius_km: float
    distance_au: float
    orbital_period_days: float
    rotation_hours: float
    mean_longitude_deg: float
    mean_motion_deg_per_day: float
    color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    fact: str
    has_rings: bool = False


SOLAR_SYSTEM_PLANETS: list[PlanetDefinition] = [
    PlanetDefinition(
        name="Mercury",
        radius_km=2439.7,
        distance_au=0.39,
        orbital_period_days=88.0,
        rotation_hours=1407.6,
        mean_longitude_deg=252.25032350,
        mean_motion_deg_per_day=149472.67411175 / 36525.0,
        color=(148, 143, 136),
        accent_color=(206, 199, 188),
        fact="The smallest planet and the closest one to the Sun.",
    ),
    PlanetDefinition(
        name="Venus",
        radius_km=6051.8,
        distance_au=0.72,
        orbital_period_days=224.7,
        rotation_hours=-5832.5,
        mean_longitude_deg=181.97909950,
        mean_motion_deg_per_day=58517.81538729 / 36525.0,
        color=(182, 152, 112),
        accent_color=(223, 198, 156),
        fact="A dense atmosphere traps heat, making Venus the hottest planet.",
    ),
    PlanetDefinition(
        name="Earth",
        radius_km=6371.0,
        distance_au=1.00,
        orbital_period_days=365.2,
        rotation_hours=23.9,
        mean_longitude_deg=100.46457166,
        mean_motion_deg_per_day=35999.37244981 / 36525.0,
        color=(92, 120, 168),
        accent_color=(182, 209, 162),
        fact="Earth is the only known planet with stable liquid water at the surface.",
    ),
    PlanetDefinition(
        name="Mars",
        radius_km=3389.5,
        distance_au=1.52,
        orbital_period_days=687.0,
        rotation_hours=24.6,
        mean_longitude_deg=-4.55343205,
        mean_motion_deg_per_day=19140.30268499 / 36525.0,
        color=(162, 108, 82),
        accent_color=(214, 170, 142),
        fact="Mars hosts Olympus Mons, the tallest volcano known in the Solar System.",
    ),
    PlanetDefinition(
        name="Jupiter",
        radius_km=69911.0,
        distance_au=5.20,
        orbital_period_days=4331.0,
        rotation_hours=9.9,
        mean_longitude_deg=34.39644051,
        mean_motion_deg_per_day=3034.74612775 / 36525.0,
        color=(183, 149, 118),
        accent_color=(228, 210, 186),
        fact="Jupiter is the largest planet and has a powerful magnetosphere.",
    ),
    PlanetDefinition(
        name="Saturn",
        radius_km=58232.0,
        distance_au=9.58,
        orbital_period_days=10747.0,
        rotation_hours=10.7,
        mean_longitude_deg=49.95424423,
        mean_motion_deg_per_day=1222.49362201 / 36525.0,
        color=(196, 177, 135),
        accent_color=(231, 220, 189),
        fact="Saturn's rings are made mostly of water ice with traces of rocky debris.",
        has_rings=True,
    ),
    PlanetDefinition(
        name="Uranus",
        radius_km=25362.0,
        distance_au=19.20,
        orbital_period_days=30589.0,
        rotation_hours=-17.2,
        mean_longitude_deg=313.23810451,
        mean_motion_deg_per_day=428.48202785 / 36525.0,
        color=(142, 186, 198),
        accent_color=(206, 232, 238),
        fact="Uranus rotates on its side, likely due to an ancient impact.",
    ),
    PlanetDefinition(
        name="Neptune",
        radius_km=24622.0,
        distance_au=30.05,
        orbital_period_days=59800.0,
        rotation_hours=16.1,
        mean_longitude_deg=-55.12002969,
        mean_motion_deg_per_day=218.45945325 / 36525.0,
        color=(92, 121, 182),
        accent_color=(175, 201, 236),
        fact="Neptune has supersonic winds and was discovered through mathematics first.",
    ),
]
