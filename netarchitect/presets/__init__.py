"""Preset loader — discovers and parses JSON scenario files."""

from __future__ import annotations

import json
from pathlib import Path

from netarchitect.models import ScenarioInput

_PRESETS_DIR = Path(__file__).parent


def list_presets() -> list[str]:
    """Return sorted basenames (without .json) of available presets."""
    return sorted(p.stem for p in _PRESETS_DIR.glob("*.json"))


def load_preset(name: str) -> ScenarioInput:
    """Load a preset JSON file by stem name and return a validated ScenarioInput."""
    path = _PRESETS_DIR / f"{name}.json"
    if not path.exists():
        available = ", ".join(list_presets())
        raise FileNotFoundError(
            f"Preset '{name}' not found. Available presets: {available}"
        )
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return ScenarioInput(**data)
