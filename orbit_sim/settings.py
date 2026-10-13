from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class StudioSettings:
    show_orbits: bool = True
    show_labels: bool = True
    show_missions: bool = True
    show_sky: bool = True
    scale_mode: str = "compressed"
    last_scene: str = "full_system"
    ui_hidden: bool = False
    master_volume: float = 0.42


def _parse_volume(value: object) -> float:
    default = StudioSettings.master_volume
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return default
    try:
        volume = float(value)
    except (ValueError, OverflowError):
        # OverflowError: an integer too large to convert to float.
        return default
    if not math.isfinite(volume):
        return default
    return max(0.0, min(1.0, volume))


_TRUE_WORDS = {"true", "1", "yes", "on"}
_FALSE_WORDS = {"false", "0", "no", "off"}


def _parse_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        word = value.strip().lower()
        if word in _TRUE_WORDS:
            return True
        if word in _FALSE_WORDS:
            return False
    return default


class StudioSettingsStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / ".gravity_studio" / "settings.json"

    def load(self) -> StudioSettings:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # Missing, unreadable, not UTF-8 or not JSON: start from defaults.
            return StudioSettings()
        if not isinstance(data, dict):
            return StudioSettings()

        return StudioSettings(
            show_orbits=_parse_bool(data.get("show_orbits"), True),
            show_labels=_parse_bool(data.get("show_labels"), True),
            show_missions=_parse_bool(data.get("show_missions"), True),
            show_sky=_parse_bool(data.get("show_sky"), True),
            scale_mode=str(data.get("scale_mode", "compressed")),
            last_scene=str(data.get("last_scene", "full_system")),
            ui_hidden=_parse_bool(data.get("ui_hidden"), False),
            master_volume=_parse_volume(data.get("master_volume")),
        )

    def save(self, settings: StudioSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
