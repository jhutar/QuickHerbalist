"""Headless tests for levels.yaml loading, strict schema validation, lookup."""

import textwrap

import pytest

from quick_herbalist.core.level_config import (
    EntityDefinition,
    LevelConfigError,
    LevelDefinition,
    level_for,
    load_levels,
)

SPRITE_NAMES = {
    "grass_sprite",
    "flower_sprite",
    "flower2_sprite",
    "stone_sprite",
    "hill_sprite",
    "spider_sprite",
    "rock_sprite",
    "background_desert_sprite",
    "background_ice_sprite",
}

VALID_YAML = """\
levels:
  - name: meadow
    background: grass_sprite
    distance: 1000
    start_speed: 3.0
    max_speed: 15.0
    entities:
      - type: flower
        sprite: flower_sprite
        interval: 1.0
      - type: stone
        sprite: stone_sprite
        interval: 3.0
        ramp_to: 0.05
"""

FLOWER_BLOCK = "      - type: flower\n        sprite: flower_sprite\n        interval: 1.0\n"
STONE_BLOCK = (
    "      - type: stone\n"
    "        sprite: stone_sprite\n"
    "        interval: 3.0\n"
    "        ramp_to: 0.05\n"
)


def _write(tmp_path, content):
    """Write YAML content to a levels file and return its path."""
    path = tmp_path / "levels.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(path)


def test_valid_load_returns_definitions(tmp_path):
    """A conforming file loads into LevelDefinition dataclasses with exact values."""
    levels = load_levels(_write(tmp_path, VALID_YAML), SPRITE_NAMES)
    assert len(levels) == 1
    level = levels[0]
    assert isinstance(level, LevelDefinition)
    assert level.name == "meadow"
    assert level.background == "grass_sprite"
    assert level.distance == 1000
    assert level.start_speed == 3.0
    assert level.max_speed == 15.0
    assert level.entities == (
        EntityDefinition(type="flower", sprite="flower_sprite", interval=1.0),
        EntityDefinition(type="stone", sprite="stone_sprite", interval=3.0, ramp_to=0.05),
    )


def test_ramp_to_optional(tmp_path):
    """Omitting ramp_to is valid and means no ramp (None)."""
    yaml_text = VALID_YAML.replace("        ramp_to: 0.05\n", "")
    levels = load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)
    assert levels[0].entities[1].ramp_to is None


def test_shipped_levels_yaml_loads():
    """The shipped levels.yaml conforms to the schema and known sprites."""
    import pathlib

    path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "src"
        / "quick_herbalist"
        / "assets"
        / "levels.yaml"
    )
    levels = load_levels(str(path), SPRITE_NAMES)
    assert [level.name for level in levels] == ["meadow", "desert", "ice"]
    assert [[entity.type for entity in level.entities] for level in levels] == [
        ["flower", "stone", "hill"],
        ["flower", "stone", "spider"],
        ["flower", "stone", "rock"],
    ]


def test_duplicate_entity_types_allowed(tmp_path):
    """Two entries of the same type (e.g. two flower sprites) are valid."""
    yaml_text = VALID_YAML.replace("      - type: stone\n", FLOWER_BLOCK + "      - type: stone\n")
    levels = load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)
    assert len(levels[0].entities) == 3


def test_unknown_top_level_key_rejected(tmp_path):
    """A not-yet-implemented option (e.g. magnetism) is a load error, not ignored."""
    yaml_text = VALID_YAML.replace(
        "    max_speed: 15.0\n", "    max_speed: 15.0\n    magnetism_bonuses: 0.5\n"
    )
    with pytest.raises(LevelConfigError, match="magnetism_bonuses"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_unknown_key_inside_entity_rejected(tmp_path):
    """Unknown keys inside entity items are load errors."""
    yaml_text = VALID_YAML.replace(
        "        interval: 1.0\n", "        interval: 1.0\n        count: 3\n"
    )
    with pytest.raises(
        LevelConfigError, match="entities\\[0\\]: unknown key\\(s\\): \\['count'\\]"
    ):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_missing_entities_rejected(tmp_path):
    """A level without an entities list is a load error."""
    yaml_text = (
        VALID_YAML.replace("    entities:\n", "").replace(FLOWER_BLOCK, "").replace(STONE_BLOCK, "")
    )
    with pytest.raises(LevelConfigError, match="'entities' must be a non-empty list"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_empty_entities_list_rejected(tmp_path):
    """An empty entities list is a load error."""
    yaml_text = (
        VALID_YAML.replace("    entities:\n", "    entities: []\n")
        .replace(FLOWER_BLOCK, "")
        .replace(STONE_BLOCK, "")
    )
    with pytest.raises(LevelConfigError, match="'entities' must be a non-empty list"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_empty_type_rejected(tmp_path):
    """An empty entity type name is a load error."""
    yaml_text = VALID_YAML.replace("      - type: flower\n", "      - type: ''\n")
    with pytest.raises(LevelConfigError, match="'type' must be a non-empty string"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_missing_required_key_rejected(tmp_path):
    """Any missing required key (here: distance) is a load error."""
    yaml_text = VALID_YAML.replace("    distance: 1000\n", "")
    with pytest.raises(LevelConfigError, match="'distance' must be a positive number"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_wrong_type_rejected(tmp_path):
    """Non-numeric distance and non-string sprite names are load errors."""
    yaml_text = VALID_YAML.replace("    distance: 1000\n", "    distance: far\n")
    with pytest.raises(LevelConfigError, match="'distance' must be a positive number"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_unknown_sprite_rejected(tmp_path):
    """Sprite names not in the sprite config are load errors, named in the message."""
    yaml_text = VALID_YAML.replace("background: grass_sprite", "background: desert_floer")
    with pytest.raises(LevelConfigError, match="unknown sprite 'desert_floer'"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_unknown_entity_sprite_rejected(tmp_path):
    """Entity sprites not in the sprite config are load errors."""
    yaml_text = VALID_YAML.replace(
        "        sprite: stone_sprite\n", "        sprite: mushroom_sprite\n"
    )
    with pytest.raises(LevelConfigError, match="unknown sprite 'mushroom_sprite'"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_duplicate_name_rejected(tmp_path):
    """Two levels sharing a name is a load error."""
    level = VALID_YAML.split("levels:\n")[1]
    yaml_text = "levels:\n" + level + level
    with pytest.raises(LevelConfigError, match="duplicate name 'meadow'"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_negative_interval_rejected(tmp_path):
    """Zero and negative intervals are load errors."""
    yaml_text = VALID_YAML.replace("        interval: 3.0\n", "        interval: -1.0\n")
    with pytest.raises(
        LevelConfigError, match="entities\\[1\\]: 'interval' must be a positive number"
    ):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_invalid_ramp_to_rejected(tmp_path):
    """A zero or negative ramp_to is a load error."""
    yaml_text = VALID_YAML.replace("        ramp_to: 0.05\n", "        ramp_to: -1\n")
    with pytest.raises(LevelConfigError, match="'ramp_to' must be a positive number"):
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)


def test_empty_levels_list_rejected(tmp_path):
    """An empty levels list is a load error."""
    with pytest.raises(LevelConfigError, match="non-empty 'levels' list"):
        load_levels(_write(tmp_path, "levels: []\n"), SPRITE_NAMES)


def test_missing_file_rejected(tmp_path):
    """A missing levels file is a load error, not a silent default."""
    with pytest.raises(LevelConfigError, match="file not found"):
        load_levels(str(tmp_path / "nope.yaml"), SPRITE_NAMES)


def test_malformed_yaml_rejected(tmp_path):
    """Broken YAML is a load error, not a crash with a raw yaml exception."""
    with pytest.raises(LevelConfigError, match="YAML parse error"):
        load_levels(_write(tmp_path, "levels: [unclosed\n"), SPRITE_NAMES)


def test_all_errors_collected(tmp_path):
    """Two bad levels report both problems in one error, not just the first."""
    yaml_text = textwrap.dedent(
        """\
        levels:
          - name: one
            background: missing_bg
            distance: -5
            start_speed: 3.0
            max_speed: 15.0
            entities:
              - type: flower
                sprite: flower_sprite
                interval: 1.0
          - name: one
            background: grass_sprite
            distance: 1000
            start_speed: 3.0
            max_speed: 15.0
            entities:
              - type: stone
                sprite: stone_sprite
                interval: 3.0
        """
    )
    with pytest.raises(LevelConfigError) as excinfo:
        load_levels(_write(tmp_path, yaml_text), SPRITE_NAMES)
    assert any("unknown sprite 'missing_bg'" in e for e in excinfo.value.errors)
    assert any("duplicate name 'one'" in e for e in excinfo.value.errors)


def _levels():
    """Two in-memory level definitions for lookup tests."""
    return [
        LevelDefinition(
            name="meadow",
            background="grass_sprite",
            distance=1000,
            start_speed=3.0,
            max_speed=15.0,
            entities=(EntityDefinition("flower", "flower_sprite", 1.0),),
        ),
        LevelDefinition(
            name="desert",
            background="grass_sprite",
            distance=1400,
            start_speed=3.4,
            max_speed=15.0,
            entities=(
                EntityDefinition("flower", "flower_sprite", 1.2),
                EntityDefinition("stone", "stone_sprite", 2.6, 0.05),
            ),
        ),
    ]


def test_level_for_is_one_based_and_repeats_last_beyond_end():
    """level_for is 1-based and repeats the last definition past the end."""
    levels = _levels()
    assert level_for(levels, 1).name == "meadow"
    assert level_for(levels, 2).name == "desert"
    assert level_for(levels, 3).name == "desert"
    assert level_for(levels, 99).name == "desert"


def test_level_for_rejects_bad_numbers():
    """level numbers below 1 or non-int raise ValueError."""
    levels = _levels()
    with pytest.raises(ValueError):
        level_for(levels, 0)
    with pytest.raises(ValueError):
        level_for(levels, 1.5)
