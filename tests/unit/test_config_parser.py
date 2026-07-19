import os
import json
import yaml
import pytest
from quick_herbalist.core.config_parser import (
    load_sprites_yaml,
    save_sprites_yaml,
    load_sprites_atlas,
    save_sprites_atlas,
    validate_configs,
)


@pytest.fixture
def temp_assets_dir(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    return assets_dir


def test_load_sprites_yaml_success(temp_assets_dir):
    yaml_path = temp_assets_dir / "sprites.yaml"
    data = {"sprites": {"hero_run": {"frames": []}}}
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    loaded_data = load_sprites_yaml(str(yaml_path))
    assert loaded_data == data


def test_load_sprites_yaml_file_not_found(temp_assets_dir):
    yaml_path = temp_assets_dir / "non_existent.yaml"
    with pytest.raises(FileNotFoundError):
        load_sprites_yaml(str(yaml_path))


def test_save_sprites_yaml_success(temp_assets_dir):
    yaml_path = temp_assets_dir / "sprites.yaml"
    data = {"sprites": {"hero_run": {"frames": []}}}

    save_sprites_yaml(str(yaml_path), data)

    with open(yaml_path, "r", encoding="utf-8") as f:
        loaded_data = yaml.safe_load(f)
    assert loaded_data == data


def test_load_sprites_atlas_success(temp_assets_dir):
    atlas_path = temp_assets_dir / "sprites.atlas"
    data = {"frames": []}
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    loaded_data = load_sprites_atlas(str(atlas_path))
    assert loaded_data == data


def test_load_sprites_atlas_file_not_found(temp_assets_dir):
    atlas_path = temp_assets_dir / "non_existent.atlas"
    with pytest.raises(FileNotFoundError):
        load_sprites_atlas(str(atlas_path))


def test_save_sprites_atlas_success(temp_assets_dir):
    atlas_path = temp_assets_dir / "sprites.atlas"
    data = {"frames": []}

    save_sprites_atlas(str(atlas_path), data)

    with open(atlas_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data


def test_validate_configs_success(temp_assets_dir):
    yaml_path = temp_assets_dir / "sprites.yaml"
    atlas_path = temp_assets_dir / "sprites.atlas"

    yaml_data = {"sprites": {"hero": {"frames": []}}}
    atlas_data = {"frames": []}

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump(atlas_data, f)

    assert validate_configs(str(yaml_path), str(atlas_path)) is True


def test_validate_configs_failure(temp_assets_dir):
    yaml_path = temp_assets_dir / "sprites.yaml"
    atlas_path = temp_assets_dir / "sprites.atlas"

    # YAML refers to an atlas_id that doesn't exist in the atlas
    yaml_data = {"sprites": {"hero": {"frames": [{"atlas_id": "missing_atlas"}]}}}
    atlas_data = {"frames": []}

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f)
    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump(atlas_data, f)

    assert validate_configs(str(yaml_path), str(atlas_path)) is False
