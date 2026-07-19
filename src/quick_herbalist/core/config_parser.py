import yaml
import json
from typing import Any, Dict

def load_sprites_yaml(path: str) -> Dict[str, Any]:
    """Loads the sprites YAML configuration."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        return data if data is not None else {}

def save_sprites_yaml(path: str, data: Dict[str, Any]) -> None:
    """Saves the sprites YAML configuration."""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, sort_keys=False)

def load_sprites_atlas(path: str) -> Dict[str, Any]:
    """Loads the sprites Atlas JSON configuration."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_sprites_atlas(path: str, data: Dict[str, Any]) -> None:
    """Saves the sprites Atlas JSON configuration."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def validate_configs(yaml_path: str, atlas_path: str) -> bool:
    """
    Validates that all atlas_ids referenced in the YAML exist in the Atlas.
    Returns True if valid, False otherwise.
    """
    try:
        yaml_data = load_sprites_yaml(yaml_path)
        atlas_data = load_sprites_atlas(atlas_path)
    except (FileNotFoundError, yaml.YAMLError, json.JSONDecodeError):
        return False

    # Flatten all atlas_ids from the atlas JSON
    all_atlas_ids = set()
    for image_regions in atlas_data.values():
        if isinstance(image_regions, dict):
            all_atlas_ids.update(image_regions.keys())

    # Check all frames in the YAML
    sprites = yaml_data.get('sprites', {})
    if not isinstance(sprites, dict):
        return False

    for sprite_name, sprite_data in sprites.items():
        if not isinstance(sprite_data, dict):
            continue
        frames = sprite_data.get('frames', [])
        if not isinstance(frames, list):
            continue
        for frame in frames:
            if not isinstance(frame, dict):
                continue
            atlas_id = frame.get('atlas_id')
            if atlas_id is None or atlas_id not in all_atlas_ids:
                # Found a missing or invalid atlas_id
                return False
    
    return True
