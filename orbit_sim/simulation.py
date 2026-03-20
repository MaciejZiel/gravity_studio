from __future__ import annotations

from orbit_sim.models import CelestialBody


class OrbitalSimulation:
    def __init__(self) -> None:
        self.bodies = [
            CelestialBody(
                name="Aster",
                orbit_radius=160,
                radius=11,
                angular_speed=0.55,
                color=(112, 181, 255),
                accent_color=(201, 229, 255),
                angle=0.9,
                starting_angle=0.9,
            )
        ]

    def update(self, dt: float) -> None:
        for body in self.bodies:
            body.angle += body.angular_speed * dt

    def reset(self) -> None:
        for body in self.bodies:
            body.reset()

