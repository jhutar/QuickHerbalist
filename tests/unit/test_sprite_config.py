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


@pytest.mark.parametrize(
    ("sprite", "yaml_data", "atlas_data", "expected_error"),
    [
        ("non_existent", None, None, "not found"),  # sprite missing from yaml
        (
            "hero_run",
            {"sprites": {"hero_run": {"frames": []}}},
            None,
            "No frames for sprite",
        ),  # sprite with an empty frame list
        (
            "hero_run",
            {"sprites": {"hero_run": {"frames": [{"duration_ms": 100}]}}},
            None,
            "no atlas_id",
        ),  # frame without atlas_id
        (
            "hero_run",
            None,
            {"hero.png": {}},
            "not found",
        ),  # unknown atlas region: raise, never fall back to a guessed image
        (
            "hero_run",
            None,
            {"hero.png": {"frame_0": [0, 0, 32]}},
            "Invalid atlas region",
        ),  # atlas rect with the wrong number of values
        (
            "hero_run",
            {"sprites": {"hero_run": {"frames": [{"atlas_id": "frame_0"}]}}},
            None,
            "duration_ms",
        ),  # frame without duration_ms
        (
            "hero_run",
            {"sprites": {"hero_run": {"frames": [{"atlas_id": "frame_0", "duration_ms": 0}]}}},
            None,
            "duration_ms",
        ),  # zero duration_ms
    ],
    ids=[
        "missing_sprite",
        "no_frames",
        "frame_without_atlas_id",
        "unknown_atlas_id",
        "invalid_region",
        "missing_duration_ms",
        "zero_duration_ms",
    ],
)
def test_resolve_frames_invalid_raises(config_files, sprite, yaml_data, atlas_data, expected_error):
    """Malformed sprite/frame/atlas data raises ValueError, never a guessed image."""
    yaml_path, atlas_path = config_files
    if yaml_data is not None:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f)
    if atlas_data is not None:
        with open(atlas_path, "w", encoding="utf-8") as f:
            json.dump(atlas_data, f)
    config = SpriteConfig(yaml_path, atlas_path)
    with pytest.raises(ValueError, match=expected_error):
        config.resolve_frames(sprite)


def _write_pair(temp_assets_dir, yaml_data, atlas_data):
    """Write a yaml/atlas pair and return (yaml_path, atlas_path) as strings.

    Each side may be a data structure (dumped) or a raw string (written verbatim).
    """
    yaml_path = temp_assets_dir / "sprites.yaml"
    atlas_path = temp_assets_dir / "sprites.atlas"
    with open(yaml_path, "w", encoding="utf-8") as f:
        if isinstance(yaml_data, str):
            f.write(yaml_data)
        else:
            yaml.dump(yaml_data, f)
    with open(atlas_path, "w", encoding="utf-8") as f:
        if isinstance(atlas_data, str):
            f.write(atlas_data)
        else:
            json.dump(atlas_data, f)
    return str(yaml_path), str(atlas_path)


@pytest.fixture
def temp_assets_dir(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    return assets_dir


@pytest.mark.parametrize(
    ("yaml_data", "atlas_data", "expected"),
    [
        ({"sprites": {"hero": {"frames": []}}}, {"frames": []}, True),  # consistent pair
        # yaml refers to an atlas_id that doesn't exist in the atlas
        ({"sprites": {"hero": {"frames": [{"atlas_id": "missing_atlas"}]}}}, {"frames": []}, False),
        # broken yaml
        ("invalid: yaml: : :", {}, False),
        # broken atlas json
        ({"sprites": {}}, "{invalid json}", False),
        # sprites is a list, not a dict
        ({"sprites": []}, {}, False),
        # frame without atlas_id
        (
            {"sprites": {"hero": {"frames": [{"duration_ms": 100}]}}},
            {"hero_region": {"hero_id": {}}},
            False,
        ),
        # frame without duration_ms
        (
            {"sprites": {"hero": {"frames": [{"atlas_id": "reg1"}]}}},
            {"img.png": {"reg1": [0, 0, 32, 32]}},
            False,
        ),
        # duration_ms is 0
        (
            {"sprites": {"hero": {"frames": [{"atlas_id": "reg1", "duration_ms": 0}]}}},
            {"img.png": {"reg1": [0, 0, 32, 32]}},
            False,
        ),
        # atlas rect has a negative value
        (
            {"sprites": {"hero": {"frames": [{"atlas_id": "reg1", "duration_ms": 100}]}}},
            {"img.png": {"reg1": [0, -1, 32, 32]}},
            False,
        ),
    ],
    ids=[
        "success",
        "unknown_atlas_id",
        "malformed_yaml",
        "malformed_atlas",
        "sprites_not_dict",
        "frame_missing_atlas_id",
        "frame_missing_duration_ms",
        "invalid_duration",
        "invalid_atlas_rect",
    ],
)
def test_validate_outcome(temp_assets_dir, yaml_data, atlas_data, expected):
    """validate() returns True only for fully consistent yaml/atlas pairs."""
    yaml_path, atlas_path = _write_pair(temp_assets_dir, yaml_data, atlas_data)
    assert SpriteConfig.validate(yaml_path, atlas_path) is expected


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
