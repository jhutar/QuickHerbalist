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
    "dandelion_sprite",
    "bluebell_sprite",
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
        sprite: dandelion_sprite
        interval: 1.0
      - type: stone
        sprite: stone_sprite
        interval: 3.0
        ramp_to: 0.05
"""

FLOWER_BLOCK = "      - type: flower\n        sprite: dandelion_sprite\n        interval: 1.0\n"
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
        EntityDefinition(type="flower", sprite="dandelion_sprite", interval=1.0),
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


@pytest.mark.parametrize(
    ("yaml_text", "expected_error"),
    [
        (None, "file not found"),  # missing file, not a silent default
        ("levels: [unclosed\n", "YAML parse error"),  # broken YAML, not a raw exception
        ("levels: []\n", "non-empty 'levels' list"),  # empty levels list
        # a not-yet-implemented option (e.g. magnetism) is an error, not ignored
        (
            VALID_YAML.replace(
                "    max_speed: 15.0\n", "    max_speed: 15.0\n    magnetism_bonuses: 0.5\n"
            ),
            "magnetism_bonuses",
        ),
        # unknown keys inside entity items
        (
            VALID_YAML.replace(
                "        interval: 1.0\n", "        interval: 1.0\n        count: 3\n"
            ),
            "entities\\[0\\]: unknown key\\(s\\)",
        ),
        # level without an entities list
        (
            VALID_YAML.replace("    entities:\n", "")
            .replace(FLOWER_BLOCK, "")
            .replace(STONE_BLOCK, ""),
            "'entities' must be a non-empty list",
        ),
        # empty entities list
        (
            VALID_YAML.replace("    entities:\n", "    entities: []\n")
            .replace(FLOWER_BLOCK, "")
            .replace(STONE_BLOCK, ""),
            "'entities' must be a non-empty list",
        ),
        # empty entity type name
        (
            VALID_YAML.replace("      - type: flower\n", "      - type: ''\n"),
            "'type' must be a non-empty string",
        ),
        # missing required key (distance)
        (
            VALID_YAML.replace("    distance: 1000\n", ""),
            "'distance' must be a positive number",
        ),
        # non-numeric distance
        (
            VALID_YAML.replace("    distance: 1000\n", "    distance: far\n"),
            "'distance' must be a positive number",
        ),
        # background sprite not in the sprite config, named in the message
        (
            VALID_YAML.replace("background: grass_sprite", "background: desert_floer"),
            "unknown sprite 'desert_floer'",
        ),
        # entity sprite not in the sprite config
        (
            VALID_YAML.replace(
                "        sprite: stone_sprite\n", "        sprite: mushroom_sprite\n"
            ),
            "unknown sprite 'mushroom_sprite'",
        ),
        # two levels sharing a name
        ("levels:\n" + VALID_YAML.split("levels:\n")[1] * 2, "duplicate name 'meadow'"),
        # negative interval
        (
            VALID_YAML.replace("        interval: 3.0\n", "        interval: -1.0\n"),
            "entities\\[1\\]: 'interval' must be a positive number",
        ),
        # negative ramp_to
        (
            VALID_YAML.replace("        ramp_to: 0.05\n", "        ramp_to: -1\n"),
            "'ramp_to' must be a positive number",
        ),
    ],
    ids=[
        "missing_file",
        "malformed_yaml",
        "empty_levels_list",
        "unknown_top_level_key",
        "unknown_key_inside_entity",
        "missing_entities",
        "empty_entities_list",
        "empty_type",
        "missing_required_key",
        "wrong_type",
        "unknown_sprite",
        "unknown_entity_sprite",
        "duplicate_name",
        "negative_interval",
        "invalid_ramp_to",
    ],
)
def test_invalid_levels_rejected(tmp_path, yaml_text, expected_error):
    """Any invalid levels file is a load error naming the problem, never a silent default."""
    if yaml_text is None:
        path = str(tmp_path / "nope.yaml")
    else:
        path = _write(tmp_path, yaml_text)
    with pytest.raises(LevelConfigError, match=expected_error):
        load_levels(path, SPRITE_NAMES)


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
                sprite: dandelion_sprite
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
            entities=(EntityDefinition("flower", "dandelion_sprite", 1.0),),
        ),
        LevelDefinition(
            name="desert",
            background="grass_sprite",
            distance=1400,
            start_speed=3.4,
            max_speed=15.0,
            entities=(
                EntityDefinition("flower", "dandelion_sprite", 1.2),
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
