"""Game-side sprite access: hands out AnimatedSprites built from resolved frames."""

from quick_herbalist.core.animated_sprite import AnimatedSprite
from quick_herbalist.core.config_parser import get_asset_path
from quick_herbalist.core.sprite_config import SpriteConfig


class SpriteManager:
    """Manage sprite definitions for the game.

    Frame resolution and config access are delegated to SpriteConfig;
    this class only wraps resolved frames in AnimatedSprite widgets.
    """

    def __init__(self, yaml_path: str = None, atlas_path: str = None):
        """Initialize SpriteManager with optional custom paths."""
        self.yaml_path = yaml_path if yaml_path is not None else get_asset_path("sprites.yaml")
        self.atlas_path = atlas_path if atlas_path is not None else get_asset_path("sprites.atlas")
        self.config = SpriteConfig(self.yaml_path, self.atlas_path)

    def get(self, sprite_name: str) -> AnimatedSprite:
        """Build an AnimatedSprite from frames resolved for the given name."""
        frames = self.config.resolve_frames(sprite_name)
        return AnimatedSprite(sprite_name, frames)
