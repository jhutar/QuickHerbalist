"""Raw file IO for sprite config assets (sprites.yaml and sprites.atlas).

Higher-level loading, frame resolution, validation, and persistence
live in quick_herbalist.core.sprite_config.
"""

import json
import os
from typing import Any

import yaml


def get_asset_path(filename: str) -> str:
    """Returns the absolute path to an asset file in the assets directory."""
    core_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_dir = os.path.dirname(core_dir)
    return os.path.join(pkg_dir, "assets", filename)


def load_sprites_yaml(path: str) -> dict[str, Any]:
    """Loads the sprites YAML configuration."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data is not None else {}


def save_sprites_yaml(path: str, data: dict[str, Any]) -> None:
    """Saves the sprites YAML configuration."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def load_sprites_atlas(path: str) -> dict[str, Any]:
    """Loads the sprites Atlas JSON configuration."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_sprites_atlas(path: str, data: dict[str, Any]) -> None:
    """Saves the sprites Atlas JSON configuration."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
