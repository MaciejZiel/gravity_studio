from __future__ import annotations

from orbit_sim.models import CelestialBody


class OrbitalSimulation:
    def __init__(self) -> None:
        self.bodies = self._default_bodies()
        self.additional_body_count = 0

    def update(self, dt: float) -> None:
        for body in self.bodies:
            body.angle += body.angular_speed * dt

    def reset(self) -> None:
        self.bodies = self._default_bodies()
        self.additional_body_count = 0

    def add_body(self) -> CelestialBody:
        body = self._generated_body(self.additional_body_count)
        self.bodies.append(body)
        self.additional_body_count += 1
        return body

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

    def _generated_body(self, index: int) -> CelestialBody:
        palette = [
            ("Lyra", (128, 150, 255), (225, 230, 255)),
            ("Solace", (255, 133, 179), (255, 221, 234)),
            ("Tide", (118, 238, 233), (218, 255, 250)),
            ("Ember", (255, 162, 112), (255, 227, 200)),
            ("Quartz", (200, 177, 255), (241, 233, 255)),
        ]
        name, color, accent = palette[index % len(palette)]
        last_radius = self.bodies[-1].orbit_radius if self.bodies else 420
        orbit_radius = last_radius + 74
        radius = max(10, 18 - (index % 4) * 2)
        angular_speed = max(0.08, 0.14 - index * 0.012)
        starting_angle = 0.85 + index * 0.9
        body_name = f"{name} {index + 1}"

        return CelestialBody(
            name=body_name,
            orbit_radius=orbit_radius,
            radius=radius,
            angular_speed=angular_speed,
            color=color,
            accent_color=accent,
            angle=starting_angle,
            starting_angle=starting_angle,
        )
