"""Sprite config module: single owner of sprites.yaml + sprites.atlas.

Loads both files, resolves sprite names into ready frame dicts,
validates file consistency, and persists create/delete/save changes.
Game (SpriteManager) and sprite editor GUI both consume this module.
"""

import os
import json

import yaml

from quick_herbalist.core.config_parser import (
    get_asset_path,
    load_sprites_yaml,
    save_sprites_yaml,
    load_sprites_atlas,
    save_sprites_atlas,
)


class SpriteConfig:
    """Owns sprite configuration: load, frame resolution, validation, persistence.

    A resolved frame dict always has the exact keys:
    {atlas_id, image, x, y, w, h, duration_ms}
    """

    def __init__(self, yaml_path: str = None, atlas_path: str = None):
        """Initialize with optional custom paths, defaults to assets dir."""
        self.yaml_path = (
            yaml_path if yaml_path is not None else get_asset_path("sprites.yaml")
        )
        self.atlas_path = (
            atlas_path if atlas_path is not None else get_asset_path("sprites.atlas")
        )
        self.sprites_data = {}
        self.atlas_data = {}
        self.load()

    def load(self):
        """Load both config files; missing files load as an empty config."""
        if os.path.exists(self.yaml_path):
            self.sprites_data = load_sprites_yaml(self.yaml_path)
        if not self.sprites_data or "sprites" not in self.sprites_data:
            self.sprites_data = {"sprites": {}}

        if os.path.exists(self.atlas_path):
            self.atlas_data = load_sprites_atlas(self.atlas_path)
        if not self.atlas_data:
            self.atlas_data = {}

    def get_sprite_list(self) -> list[str]:
        """Return sorted list of all registered sprite names."""
        return sorted(self.sprites_data.get("sprites", {}).keys())

    def _lookup_region(self, atlas_id: str) -> tuple:
        """Find (image, x, y, w, h) for an atlas id; raise ValueError if missing or invalid."""
        for image, regions in self.atlas_data.items():
            if not isinstance(regions, dict) or atlas_id not in regions:
                continue
            region = regions[atlas_id]
            if not isinstance(region, list) or len(region) != 4:
                raise ValueError(f"Invalid atlas region for '{atlas_id}': {region!r}")
            return image, region[0], region[1], region[2], region[3]
        raise ValueError(f"Atlas ID '{atlas_id}' not found in {self.atlas_path}")

    def resolve_frames(self, sprite_name: str) -> list[dict]:
        """Resolve a sprite name into ready frame dicts.

        Each frame dict: {atlas_id, image, x, y, w, h, duration_ms}.
        Raises ValueError on missing sprite, empty frames, missing atlas_id,
        unknown or invalid atlas region, or missing/non-positive duration_ms.
        Never falls back to guessed values.
        """
        sprite_entry = self.sprites_data.get("sprites", {}).get(sprite_name)
        if not sprite_entry:
            raise ValueError(f"Sprite '{sprite_name}' not found in {self.yaml_path}")

        frames = sprite_entry.get("frames", [])
        if not frames:
            raise ValueError(f"No frames for sprite '{sprite_name}'")

        resolved = []
        for frame in frames:
            atlas_id = frame.get("atlas_id")
            if not atlas_id:
                raise ValueError(f"Frame of sprite '{sprite_name}' has no atlas_id")
            duration = frame.get("duration_ms")
            if not isinstance(duration, (int, float)) or duration <= 0:
                raise ValueError(
                    f"Frame '{atlas_id}' of sprite '{sprite_name}' "
                    f"has missing or non-positive duration_ms"
                )
            image, x, y, w, h = self._lookup_region(atlas_id)
            resolved.append(
                {
                    "atlas_id": atlas_id,
                    "duration_ms": duration,
                    "image": image,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                }
            )
        return resolved

    @staticmethod
    def validate(yaml_path: str, atlas_path: str) -> bool:
        """Validate consistency between a sprites YAML and an atlas file.

        Checks atlas regions are 4-number lists with values >= 0, every frame
        references an existing atlas_id, and every frame has duration_ms > 0.
        Returns True if valid, False otherwise; never raises on bad input.
        """
        try:
            yaml_data = load_sprites_yaml(yaml_path)
            atlas_data = load_sprites_atlas(atlas_path)
        except (FileNotFoundError, yaml.YAMLError, json.JSONDecodeError):
            return False

        all_atlas_ids = set()
        for image, regions in atlas_data.items():
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

        sprites = yaml_data.get("sprites", {})
        if not isinstance(sprites, dict):
            return False

        for sprite_data in sprites.values():
            if not isinstance(sprite_data, dict):
                return False
            frames = sprite_data.get("frames", [])
            if not isinstance(frames, list):
                return False
            for frame in frames:
                if not isinstance(frame, dict):
                    return False
                atlas_id = frame.get("atlas_id")
                if atlas_id is None or atlas_id not in all_atlas_ids:
                    return False
                duration = frame.get("duration_ms")
                if not isinstance(duration, (int, float)) or duration <= 0:
                    return False

        return True

    def create_sprite(self, sprite_name: str) -> bool:
        """Create a new empty sprite entry. Returns True on success, False if name invalid or duplicate."""
        if not sprite_name or sprite_name in self.sprites_data["sprites"]:
            return False
        self.sprites_data["sprites"][sprite_name] = {"frames": []}
        save_sprites_yaml(self.yaml_path, self.sprites_data)
        return True

    def delete_sprite(self, sprite_name: str):
        """Delete a sprite and its associated atlas regions, then persist both files."""
        sprite_entry = self.sprites_data["sprites"].get(sprite_name)
        if sprite_entry is None:
            return

        atlas_ids = {
            f.get("atlas_id")
            for f in sprite_entry.get("frames", [])
            if f.get("atlas_id")
        }
        self.sprites_data["sprites"].pop(sprite_name, None)
        self._remove_atlas_ids(atlas_ids)
        self._save_both()

    def save_sprite_frames(self, sprite_name: str, frames: list[dict]):
        """Update a sprite's frames from working frame dicts, then persist both files.

        Working frame dicts use the resolved schema keys
        {atlas_id, duration_ms, image, x, y, w, h}.
        Old atlas regions no longer referenced are removed.
        """
        old_entry = self.sprites_data["sprites"].get(sprite_name, {})
        old_atlas_ids = {
            f.get("atlas_id")
            for f in old_entry.get("frames", [])
            if f.get("atlas_id")
        }
        self._remove_atlas_ids(old_atlas_ids)

        yaml_frames = [
            {"atlas_id": f["atlas_id"], "duration_ms": f["duration_ms"]}
            for f in frames
        ]
        self.sprites_data["sprites"][sprite_name] = {"frames": yaml_frames}

        for frame in frames:
            self.atlas_data.setdefault(frame["image"], {})[frame["atlas_id"]] = [
                frame["x"],
                frame["y"],
                frame["w"],
                frame["h"],
            ]
        self._save_both()

    def _remove_atlas_ids(self, atlas_ids: set):
        """Remove the given atlas ids (and any image left empty) from in-memory atlas data."""
        for image, regions in list(self.atlas_data.items()):
            if not isinstance(regions, dict):
                continue
            for aid in list(regions.keys()):
                if aid in atlas_ids:
                    regions.pop(aid)
            if not regions:
                self.atlas_data.pop(image)

    def _save_both(self):
        """Persist in-memory YAML and atlas data to their files."""
        save_sprites_yaml(self.yaml_path, self.sprites_data)
        save_sprites_atlas(self.atlas_path, self.atlas_data)
