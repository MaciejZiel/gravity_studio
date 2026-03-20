from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class StudioSettings:
    show_orbits: bool = True
    show_labels: bool = True
    scale_mode: str = "compressed"
    last_scene: str = "full_system"
    ui_hidden: bool = False
    master_volume: float = 0.42


class StudioSettingsStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / ".gravity_studio" / "settings.json"

    def load(self) -> StudioSettings:
        try:
            data = json.loads(self.path.read_text())
        except FileNotFoundError:
            return StudioSettings()
        except json.JSONDecodeError:
            return StudioSettings()

        return StudioSettings(
            show_orbits=bool(data.get("show_orbits", True)),
            show_labels=bool(data.get("show_labels", True)),
            scale_mode=str(data.get("scale_mode", "compressed")),
            last_scene=str(data.get("last_scene", "full_system")),
            ui_hidden=bool(data.get("ui_hidden", False)),
            master_volume=max(0.0, min(1.0, float(data.get("master_volume", 0.42)))),
        )

    def save(self, settings: StudioSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2))
