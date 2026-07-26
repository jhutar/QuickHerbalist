from quick_herbalist.core.config_parser import (
    load_sprites_yaml,
    load_sprites_atlas,
    get_asset_path,
)
from quick_herbalist.core.animated_sprite import AnimatedSprite


class SpriteManager:
    def __init__(self, yaml_path: str = None, atlas_path: str = None):
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
        self.sprites_data = load_sprites_yaml(self.yaml_path)
        self.atlas_data = load_sprites_atlas(self.atlas_path)

    def get(self, sprite_name: str) -> AnimatedSprite:
        # Check if sprite exists in data
        sprite_entry = self.sprites_data.get("sprites", {}).get(sprite_name)
        if not sprite_entry:
            raise ValueError(f"Sprite '{sprite_name}' not found in {self.yaml_path}")

        return AnimatedSprite(sprite_name, self.sprites_data, self.atlas_data)
