from __future__ import annotations

from orbit_sim.models import CelestialBody


class OrbitalSimulation:
    def __init__(self) -> None:
        self.bodies = self._default_bodies()

    def update(self, dt: float) -> None:
        for body in self.bodies:
            body.angle += body.angular_speed * dt

    def reset(self) -> None:
        for body in self.bodies:
            body.reset()

    def _default_bodies(self) -> list[CelestialBody]:
        return [
            CelestialBody(
                name="Aster",
                orbit_radius=122,
                radius=9,
                angular_speed=0.92,
                color=(124, 194, 255),
                accent_color=(220, 239, 255),
                angle=0.9,
                starting_angle=0.9,
            ),
            CelestialBody(
                name="Vela",
                orbit_radius=186,
                radius=14,
                angular_speed=0.58,
                color=(104, 233, 202),
                accent_color=(213, 255, 244),
                angle=2.35,
                starting_angle=2.35,
            ),
            CelestialBody(
                name="Cinder",
                orbit_radius=268,
                radius=18,
                angular_speed=0.34,
                color=(255, 143, 115),
                accent_color=(255, 227, 208),
                angle=4.7,
                starting_angle=4.7,
            ),
            CelestialBody(
                name="Noctis",
                orbit_radius=356,
                radius=24,
                angular_speed=0.24,
                color=(180, 138, 255),
                accent_color=(237, 222, 255),
                angle=1.95,
                starting_angle=1.95,
            ),
            CelestialBody(
                name="Halo",
                orbit_radius=448,
                radius=16,
                angular_speed=0.17,
                color=(244, 198, 110),
                accent_color=(255, 236, 195),
                angle=5.25,
                starting_angle=5.25,
            ),
        ]
