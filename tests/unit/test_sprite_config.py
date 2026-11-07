"""Unit tests for the core SpriteConfig module (load, resolve, validate, persist)."""

import json

import pytest
import yaml

from quick_herbalist.core.sprite_config import SpriteConfig


@pytest.fixture
def config_files(tmp_path):
    """Create a valid sprites.yaml and sprites.atlas pair in a temp dir."""
    yaml_path = tmp_path / "sprites.yaml"
    atlas_path = tmp_path / "sprites.atlas"
    yaml_path.write_text(
        """
sprites:
  hero_run:
    frames:
      - atlas_id: frame_0
        duration_ms: 100
      - atlas_id: frame_1
        duration_ms: 200
""",
        encoding="utf-8",
    )
    atlas_path.write_text(
        json.dumps({"hero.png": {"frame_0": [0, 0, 32, 32], "frame_1": [32, 0, 32, 32]}}),
        encoding="utf-8",
    )
    return str(yaml_path), str(atlas_path)


@pytest.fixture
def config(config_files):
    """SpriteConfig loaded from the temp config files."""
    yaml_path, atlas_path = config_files
    return SpriteConfig(yaml_path, atlas_path)


def test_load_missing_files_yields_empty_config(tmp_path):
    config = SpriteConfig(str(tmp_path / "none.yaml"), str(tmp_path / "none.atlas"))
    assert config.sprites_data == {"sprites": {}}
    assert config.atlas_data == {}
    assert config.get_sprite_list() == []


def test_get_sprite_list_sorted(config):
    assert config.get_sprite_list() == ["hero_run"]


def test_resolve_frames_success(config):
    frames = config.resolve_frames("hero_run")
    assert frames == [
        {
            "atlas_id": "frame_0",
            "duration_ms": 100,
            "image": "hero.png",
            "x": 0,
            "y": 0,
            "w": 32,
            "h": 32,
        },
        {
            "atlas_id": "frame_1",
            "duration_ms": 200,
            "image": "hero.png",
            "x": 32,
            "y": 0,
            "w": 32,
            "h": 32,
        },
    ]


def test_resolve_frames_missing_sprite(config):
    with pytest.raises(ValueError, match="not found"):
        config.resolve_frames("non_existent")


def test_resolve_frames_no_frames(config_files):
    yaml_path, atlas_path = config_files
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("sprites: { hero_run: { frames: [] } }")
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="No frames for sprite"):
        config.resolve_frames("hero_run")


def test_resolve_frames_frame_without_atlas_id(config_files):
    yaml_path, atlas_path = config_files
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump({"sprites": {"hero_run": {"frames": [{"duration_ms": 100}]}}}, f)
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="no atlas_id"):
        config.resolve_frames("hero_run")


def test_resolve_frames_unknown_atlas_id_raises_no_guessing(config_files):
    """Missing atlas region must raise, never fall back to a guessed image."""
    yaml_path, atlas_path = config_files
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump({"hero.png": {}}, f)
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="not found"):
        config.resolve_frames("hero_run")


def test_resolve_frames_invalid_region_raises(config_files):
    yaml_path, atlas_path = config_files
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump({"hero.png": {"frame_0": [0, 0, 32]}}, f)
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="Invalid atlas region"):
        config.resolve_frames("hero_run")


def test_resolve_frames_missing_duration_ms_raises(config_files):
    yaml_path, atlas_path = config_files
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump({"sprites": {"hero_run": {"frames": [{"atlas_id": "frame_0"}]}}}, f)
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="duration_ms"):
        config.resolve_frames("hero_run")


def test_resolve_frames_zero_duration_ms_raises(config_files):
    yaml_path, atlas_path = config_files
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(
            {"sprites": {"hero_run": {"frames": [{"atlas_id": "frame_0", "duration_ms": 0}]}}},
            f,
        )
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match="duration_ms"):
        config.resolve_frames("hero_run")


def _write_pair(temp_assets_dir, yaml_data, atlas_data):
    """Write a yaml/atlas pair and return (yaml_path, atlas_path) as strings."""
    yaml_path = temp_assets_dir / "sprites.yaml"
    atlas_path = temp_assets_dir / "sprites.atlas"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump(atlas_data, f)
    return str(yaml_path), str(atlas_path)


@pytest.fixture
def temp_assets_dir(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    return assets_dir


def test_validate_success(temp_assets_dir):
    yaml_path, atlas_path = _write_pair(
        temp_assets_dir,
        {"sprites": {"hero": {"frames": []}}},
        {"frames": []},
    )
    assert SpriteConfig.validate(yaml_path, atlas_path) is True


def test_validate_unknown_atlas_id(temp_assets_dir):
    # YAML refers to an atlas_id that doesn't exist in the atlas
    yaml_path, atlas_path = _write_pair(
        temp_assets_dir,
        {"sprites": {"hero": {"frames": [{"atlas_id": "missing_atlas"}]}}},
        {"frames": []},
    )
    assert SpriteConfig.validate(yaml_path, atlas_path) is False


def test_validate_malformed_yaml(temp_assets_dir):
    yaml_path = temp_assets_dir / "sprites.yaml"
    atlas_path = temp_assets_dir / "sprites.atlas"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("invalid: yaml: : :")
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump({}, f)
    assert SpriteConfig.validate(str(yaml_path), str(atlas_path)) is False


def test_validate_malformed_atlas(temp_assets_dir):
    yaml_path = temp_assets_dir / "sprites.yaml"
    atlas_path = temp_assets_dir / "sprites.atlas"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump({"sprites": {}}, f)
    with open(atlas_path, "w", encoding="utf-8") as f:
        f.write("{invalid json}")
    assert SpriteConfig.validate(str(yaml_path), str(atlas_path)) is False


def test_validate_sprites_not_dict(temp_assets_dir):
    # sprites is a list, not a dict
    yaml_path, atlas_path = _write_pair(temp_assets_dir, {"sprites": []}, {})
    assert SpriteConfig.validate(yaml_path, atlas_path) is False


def test_validate_frame_missing_atlas_id(temp_assets_dir):
    yaml_path, atlas_path = _write_pair(
        temp_assets_dir,
        {"sprites": {"hero": {"frames": [{"duration_ms": 100}]}}},
        {"hero_region": {"hero_id": {}}},
    )
    assert SpriteConfig.validate(yaml_path, atlas_path) is False


def test_validate_frame_missing_duration_ms(temp_assets_dir):
    yaml_path, atlas_path = _write_pair(
        temp_assets_dir,
        {"sprites": {"hero": {"frames": [{"atlas_id": "reg1"}]}}},
        {"img.png": {"reg1": [0, 0, 32, 32]}},
    )
    assert SpriteConfig.validate(yaml_path, atlas_path) is False


def test_validate_invalid_duration(temp_assets_dir):
    # duration_ms is 0
    yaml_path, atlas_path = _write_pair(
        temp_assets_dir,
        {"sprites": {"hero": {"frames": [{"atlas_id": "reg1", "duration_ms": 0}]}}},
        {"img.png": {"reg1": [0, 0, 32, 32]}},
    )
    assert SpriteConfig.validate(yaml_path, atlas_path) is False


def test_validate_invalid_atlas_rect(temp_assets_dir):
    # Atlas rect has negative value
    yaml_path, atlas_path = _write_pair(
        temp_assets_dir,
        {"sprites": {"hero": {"frames": [{"atlas_id": "reg1", "duration_ms": 100}]}}},
        {"img.png": {"reg1": [0, -1, 32, 32]}},
    )
    assert SpriteConfig.validate(yaml_path, atlas_path) is False


def test_create_sprite_success(config):
    assert config.create_sprite("new_sprite") is True
    assert "new_sprite" in config.sprites_data["sprites"]
    assert config.sprites_data["sprites"]["new_sprite"] == {"frames": []}

    # Persisted to the yaml file
    with open(config.yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "new_sprite" in data["sprites"]


def test_create_sprite_duplicate_or_invalid(config):
    assert config.create_sprite("hero_run") is False
    assert config.create_sprite("") is False


def test_delete_sprite_cleans_atlas(config):
    config.delete_sprite("hero_run")
    assert "hero_run" not in config.sprites_data["sprites"]
    assert config.atlas_data == {}

    with open(config.atlas_path, encoding="utf-8") as f:
        assert json.load(f) == {}


def test_delete_unknown_sprite_is_noop(config):
    config.delete_sprite("non_existent")
    assert "hero_run" in config.sprites_data["sprites"]


def test_save_sprite_frames_persists_both_files(config):
    frames = [
        {
            "atlas_id": "frame_0",
            "duration_ms": 100,
            "image": "hero.png",
            "x": 0,
            "y": 0,
            "w": 32,
            "h": 32,
        },
        {
            "atlas_id": "frame_1",
            "duration_ms": 150,
            "image": "hero.png",
            "x": 32,
            "y": 0,
            "w": 32,
            "h": 32,
        },
    ]
    config.save_sprite_frames("hero_run", frames)

    with open(config.yaml_path, encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)
    saved_frames = yaml_data["sprites"]["hero_run"]["frames"]
    assert saved_frames == [
        {"atlas_id": "frame_0", "duration_ms": 100},
        {"atlas_id": "frame_1", "duration_ms": 150},
    ]

    with open(config.atlas_path, encoding="utf-8") as f:
        atlas_data = json.load(f)
    assert atlas_data["hero.png"]["frame_1"] == [32, 0, 32, 32]


def test_save_sprite_frames_removes_old_atlas_ids(config):
    frames = [
        {
            "atlas_id": "brand_new",
            "duration_ms": 100,
            "image": "other.png",
            "x": 5,
            "y": 6,
            "w": 10,
            "h": 12,
        },
    ]
    config.save_sprite_frames("hero_run", frames)

    # Old frame_0/frame_1 regions and their image are gone
    assert "hero.png" not in config.atlas_data
    assert config.atlas_data["other.png"]["brand_new"] == [5, 6, 10, 12]
