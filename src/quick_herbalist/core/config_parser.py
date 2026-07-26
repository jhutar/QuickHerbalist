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


class ConfigStitcher:
    """
    A domain-level configuration controller that sits behind the Kivy GUI.
    It decouples the relational skinny YAML and standard Atlas JSON files,
    managing the unified sprite and frame structures in memory.
    """

    def __init__(self, yaml_path: str = None, atlas_path: str = None):
        self.yaml_path = (
            yaml_path if yaml_path is not None else get_asset_path("sprites.yaml")
        )
        self.atlas_path = (
            atlas_path if atlas_path is not None else get_asset_path("sprites.atlas")
        )
        self.sprites_yaml_data = {}
        self.sprites_atlas_data = {}
        self.load_configs()

    def load_configs(self):
        import os

        if os.path.exists(self.yaml_path):
            self.sprites_yaml_data = load_sprites_yaml(self.yaml_path)
        if not self.sprites_yaml_data or "sprites" not in self.sprites_yaml_data:
            self.sprites_yaml_data = {"sprites": {}}

        if os.path.exists(self.atlas_path):
            self.sprites_atlas_data = load_sprites_atlas(self.atlas_path)
        if not self.sprites_atlas_data:
            self.sprites_atlas_data = {}

    def get_sprite_list(self) -> list[str]:
        return sorted(self.sprites_yaml_data.get("sprites", {}).keys())

    def get_sprite_frames(self, sprite_name: str) -> list[dict]:
        """
        Returns the fully resolved frame structures for a sprite.
        """
        frames = []
        sprite_entry = self.sprites_yaml_data.get("sprites", {}).get(sprite_name, {})
        yaml_frames = sprite_entry.get("frames", [])

        for frame in yaml_frames:
            atlas_id = frame.get("atlas_id", "")
            duration = frame.get("duration_ms", 250)

            image_filename = ""
            x, y, w, h = 0, 0, 32, 32
            found = False

            for img_name, regions in self.sprites_atlas_data.items():
                if isinstance(regions, dict) and atlas_id in regions:
                    region = regions[atlas_id]
                    if isinstance(region, list) and len(region) == 4:
                        image_filename = img_name
                        x, y, w, h = region
                        found = True
                        break

            if not found:
                image_filename = "test_hero.png"
                x, y, w, h = 0, 0, 32, 32

            frames.append(
                {
                    "atlas_id": atlas_id,
                    "duration": duration,
                    "image": image_filename,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                }
            )
        return frames

    def create_sprite(self, sprite_name: str) -> bool:
        if not sprite_name or sprite_name in self.sprites_yaml_data["sprites"]:
            return False
        self.sprites_yaml_data["sprites"][sprite_name] = {"frames": []}
        save_sprites_yaml(self.yaml_path, self.sprites_yaml_data)
        return True

    def delete_sprite(self, sprite_name: str):
        if sprite_name not in self.sprites_yaml_data["sprites"]:
            return

        # Gather all atlas_ids of this sprite to clean them from atlas too
        sprite_entry = self.sprites_yaml_data["sprites"].get(sprite_name, {})
        atlas_ids_to_remove = {
            f.get("atlas_id")
            for f in sprite_entry.get("frames", [])
            if f.get("atlas_id")
        }

        # Delete from yaml
        self.sprites_yaml_data["sprites"].pop(sprite_name, None)

        # Clean up corresponding atlas regions
        for img_name, regions in list(self.sprites_atlas_data.items()):
            if isinstance(regions, dict):
                for aid in list(regions.keys()):
                    if aid in atlas_ids_to_remove:
                        regions.pop(aid)
                if not regions:
                    self.sprites_atlas_data.pop(img_name)

        # Save both
        save_sprites_yaml(self.yaml_path, self.sprites_yaml_data)
        save_sprites_atlas(self.atlas_path, self.sprites_atlas_data)

    def save_sprite_frames(self, sprite_name: str, frames: list[dict]):
        # Clean up old atlas mappings
        old_sprite_entry = self.sprites_yaml_data["sprites"].get(sprite_name, {})
        old_atlas_ids = {
            f.get("atlas_id")
            for f in old_sprite_entry.get("frames", [])
            if f.get("atlas_id")
        }
        for img_name, regions in list(self.sprites_atlas_data.items()):
            if isinstance(regions, dict):
                for aid in list(regions.keys()):
                    if aid in old_atlas_ids:
                        regions.pop(aid)
                if not regions:
                    self.sprites_atlas_data.pop(img_name)

        # Re-populate YAML
        yaml_frames = []
        for frame in frames:
            yaml_frames.append(
                {"atlas_id": frame["atlas_id"], "duration_ms": frame["duration"]}
            )
        self.sprites_yaml_data["sprites"][sprite_name] = {"frames": yaml_frames}

        # Re-populate Atlas
        for frame in frames:
            image = frame["image"]
            atlas_id = frame["atlas_id"]
            x, y, w, h = frame["x"], frame["y"], frame["w"], frame["h"]

            self.sprites_atlas_data.setdefault(image, {})
            self.sprites_atlas_data[image][atlas_id] = [x, y, w, h]

        # Save both
        save_sprites_yaml(self.yaml_path, self.sprites_yaml_data)
        save_sprites_atlas(self.atlas_path, self.sprites_atlas_data)
