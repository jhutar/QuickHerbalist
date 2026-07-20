import sys
import pytest
from unittest.mock import MagicMock
import types

# 1. Setup mocks for Kivy BEFORE importing anything that uses it
kivy_module = types.ModuleType("kivy")
kivy_uix_module = types.ModuleType("kivy.uix")
kivy_widget_module = types.ModuleType("kivy.uix.widget")
kivy_core_module = types.ModuleType("kivy.core")
kivy_core_image_module = types.ModuleType("kivy.core.image")
kivy_clock_module = types.ModuleType("kivy.clock")
kivy_graphics_module = types.ModuleType("kivy.graphics")


# Define a real class for Widget to allow inheritance
class RealWidget:
    def __init__(self, **kwargs):
        self.canvas = MagicMock()
        self.size = (100, 100)
        self.pos = (0, 0)
        self.children = []

    def add_widget(self, *args, **kwargs):
        pass

    def remove_widget(self, *args, **kwargs):
        pass


kivy_widget_module.Widget = RealWidget

kivy_uix_module.widget = kivy_widget_module
kivy_module.uix = kivy_uix_module
kivy_module.core = kivy_core_module
kivy_core_module.image = kivy_core_image_module
kivy_core_module.graphics = kivy_graphics_module
kivy_module.clock = kivy_clock_module

# Setup submodules properly for the imports
sys.modules["kivy"] = kivy_module
sys.modules["kivy.uix"] = kivy_uix_module
sys.modules["kivy.uix.widget"] = kivy_widget_module
sys.modules["kivy.core"] = kivy_core_module
sys.modules["kivy.core.image"] = kivy_core_image_module
sys.modules["kivy.clock"] = kivy_clock_module
sys.modules["kivy.graphics"] = kivy_graphics_module

# Mocking Kivy components
kivy_core_image_module.Image = MagicMock()
kivy_core_image_module.Image.return_value.texture.get_region.return_value = MagicMock()

kivy_graphics_module.Rectangle = MagicMock()
kivy_graphics_module.Color = MagicMock()
kivy_clock_module.Clock = MagicMock()
kivy_clock_module.Clock.schedule_interval = MagicMock()

# 2. Import the code under test
from quick_herbalist.core.sprite_manager import SpriteManager  # noqa: E402


@pytest.fixture
def dummy_configs(tmp_path):
    yaml_file = tmp_path / "sprites.yaml"
    atlas_file = tmp_path / "sprites.atlas"
    yaml_file.write_text(
        """
sprites:
  hero_run:
    frames:
      - atlas_id: frame_0
        duration_ms: 100
      - atlas_id: frame_1
        duration_ms: 100
""",
        encoding="utf-8",
    )
    atlas_file.write_text(
        """
{
  "hero.png": {
    "frame_0": [0, 0, 32, 32],
    "frame_1": [32, 0, 32, 32]
  }
}
""",
        encoding="utf-8",
    )
    return str(yaml_file), str(atlas_file)


def test_sprite_manager_get_success(dummy_configs):
    yaml_path, atlas_path = dummy_configs
    sm = SpriteManager(yaml_path, atlas_path)
    sprite = sm.get("hero_run")
    assert sprite.sprite_name == "hero_run"
    assert len(sprite.frames_data) == 2


def test_sprite_manager_not_found(dummy_configs):
    yaml_path, atlas_path = dummy_configs
    sm = SpriteManager(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="not found"):
        sm.get("non_existent")


def test_sprite_manager_no_frames(dummy_configs):
    yaml_path, atlas_path = dummy_configs
    with open(yaml_path, "w") as f:
        f.write("sprites: { hero_run: { frames: [] } }")
    sm = SpriteManager(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="No frames for sprite"):
        sm.get("hero_run")


def test_animated_sprite_update(dummy_configs):
    yaml_path, atlas_path = dummy_configs
    sm = SpriteManager(yaml_path, atlas_path)
    sprite = sm.get("hero_run")
    sprite.update(0.2)
    assert sprite.current_frame_index == 1
    sprite.update(0.2)
    assert sprite.current_frame_index == 0
