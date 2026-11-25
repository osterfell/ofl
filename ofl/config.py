"""Where the API key lives: $OFL_API_KEY, else ~/.config/ofl/config.json."""

from __future__ import annotations

import json
import os
from pathlib import Path


def path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "ofl" / "config.json"


def load() -> dict:
    try:
        return json.loads(path().read_text())
    except (OSError, ValueError):
        return {}


def save(values: dict) -> None:
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(values, indent=2) + "\n")
    target.chmod(0o600)


def api_key() -> str:
    return os.environ.get("OFL_API_KEY") or load().get("api_key", "")
