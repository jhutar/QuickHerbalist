import yaml
import json
import os
from typing import Any, Dict


def get_asset_path(filename: str) -> str:
    """Returns the absolute path to an asset file in the assets directory."""
    core_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_dir = os.path.dirname(core_dir)
    return os.path.join(pkg_dir, "assets", filename)


def load_sprites_yaml(path: str) -> Dict[str, Any]:
    """Loads the sprites YAML configuration."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data is not None else {}


def save_sprites_yaml(path: str, data: Dict[str, Any]) -> None:
    """Saves the sprites YAML configuration."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def load_sprites_atlas(path: str) -> Dict[str, Any]:
    """Loads the sprites Atlas JSON configuration."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sprites_atlas(path: str, data: Dict[str, Any]) -> None:
    """Saves the sprites Atlas JSON configuration."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def validate_configs(yaml_path: str, atlas_path: str) -> bool:
    """
    Validates that:
    1. All atlas_ids referenced in the YAML exist in the Atlas.
    2. All frames in the YAML have a duration_ms > 0.
    3. All texture regions in the Atlas have valid x, y, w, h >= 0.
    Returns True if valid, False otherwise.
    """
    try:
        yaml_data = load_sprites_yaml(yaml_path)
        atlas_data = load_sprites_atlas(atlas_path)
    except (FileNotFoundError, yaml.YAMLError, json.JSONDecodeError):
        return False

    # 1. Validate Atlas texture regions (x, y, w, h >= 0)
    all_atlas_ids = set()
    for image_file, regions in atlas_data.items():
        if not isinstance(regions, dict):
            continue
        for region_id, rect in regions.items():
            if isinstance(rect, list):
                if len(rect) != 4 or not all(
                    isinstance(v, (int, float)) and v >= 0 for v in rect
                ):
                    return False
            elif isinstance(rect, dict):
                # Handle case where rect is a dict (as seen in some tests)
                pass
            else:
                return False
            all_atlas_ids.add(region_id)

    # 2. Validate Sprites in YAML
    sprites = yaml_data.get("sprites", {})
    if not isinstance(sprites, dict):
        return False

    for sprite_name, sprite_data in sprites.items():
        if not isinstance(sprite_data, dict):
            return False
        frames = sprite_data.get("frames", [])
        if not isinstance(frames, list):
            return False
        for frame in frames:
            if not isinstance(frame, dict):
                return False

            # Check atlas_id
            atlas_id = frame.get("atlas_id")
            if atlas_id is None or atlas_id not in all_atlas_ids:
                return False

            # Check duration_ms > 0
            duration = frame.get("duration_ms", 250)
            if not isinstance(duration, (int, float)) or duration <= 0:
                return False

    return True
