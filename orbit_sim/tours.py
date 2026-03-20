from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TourStep:
    key: str
    title: str
    caption: str
    scene_mode: str
    duration: float
    focus_body: str | None = None
    jump_action: str | None = None
    scale_story: bool = False


@dataclass(frozen=True)
class TourDefinition:
    action: str
    label: str
    description: str
    steps: tuple[TourStep, ...]


TOUR_DEFINITIONS: tuple[TourDefinition, ...] = (
    TourDefinition(
        action="tour_grand",
        label="Grand Tour",
        description="A cinematic pass from the rocky inner worlds out to the edge of the giant planets.",
        steps=(
            TourStep("opening", "Solar System", "The full architecture of the planetary system in one frame.", "full_system", 5.0),
            TourStep("inner", "Inner Worlds", "Mercury through Mars reveal how tightly packed the rocky planets are.", "inner_worlds", 6.0),
            TourStep("earth", "Earth System", "A close-up of Earth, the Moon and near-Earth exploration paths.", "focus", 6.0, focus_body="Earth"),
            TourStep("jupiter", "Gas Giant Scale", "Jupiter dominates the outer system with its Galilean satellites.", "focus", 6.0, focus_body="Jupiter"),
            TourStep("saturn", "Rings in Motion", "Saturn's ring plane and Titan bring the scene into cinematic territory.", "focus", 7.0, focus_body="Saturn"),
            TourStep("outer", "Outer Reach", "Uranus and Neptune sit in immense stretches of empty space.", "outer_worlds", 6.0),
            TourStep("story", "Scale Story", "This pass relaxes the compressed view toward a harsher sense of real distance.", "full_system", 7.0, scale_story=True),
        ),
    ),
    TourDefinition(
        action="tour_history",
        label="Historic Dates",
        description="Jumps through moments that changed how humanity sees the Solar System.",
        steps=(
            TourStep("apollo", "Apollo 11", "Humanity's first crewed lunar landing happened inside the Earth-Moon system.", "focus", 6.0, focus_body="Earth", jump_action="jump_apollo"),
            TourStep("voyager", "Voyager Era", "Voyager 1 began the mission that redefined the outer planets.", "gas_giants", 6.0, jump_action="jump_voyager"),
            TourStep("equinox", "Equinox Geometry", "At equinox the solar lighting across Earth is especially legible.", "inner_worlds", 5.0, jump_action="jump_equinox"),
            TourStep("solstice", "Solstice Tilt", "Seasonal lighting shifts become obvious in planetary close-ups.", "inner_worlds", 5.0, jump_action="jump_solstice"),
            TourStep("now", "Now", "Return to the current live arrangement of the planets.", "full_system", 5.0, jump_action="jump_now"),
        ),
    ),
)
