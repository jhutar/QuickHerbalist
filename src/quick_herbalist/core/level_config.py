"""Load and validate user-authored level definitions (levels.yaml).

Pure Python, no Kivy imports, so the schema and lookup logic are
testable headless. Fail fast: any schema violation, duplicate name, or
unknown sprite name produces a LevelConfigError listing every problem
found, never a partial load.
"""

import logging
from dataclasses import dataclass

import yaml

logger = logging.getLogger(__name__)

_LEVEL_KEYS = {"name", "background", "distance", "start_speed", "max_speed", "entities"}
_ENTITY_KEYS = {"type", "sprite", "interval", "ramp_to"}


class LevelConfigError(ValueError):
    """Raised when levels.yaml fails validation; message lists all errors."""

    def __init__(self, errors: list[str]):
        """Create the error from a list of human-readable problem strings."""
        super().__init__("levels.yaml invalid:\n" + "\n".join(f"  - {e}" for e in errors))
        self.errors = errors


@dataclass(frozen=True)
class EntityDefinition:
    """One spawnable entity type of a level: kind, sprite, spawn pacing.

    ramp_to None means the interval stays constant for the whole level;
    otherwise each spawn shrinks the interval toward that floor.
    """

    type: str
    sprite: str
    interval: float
    ramp_to: float | None = None


@dataclass(frozen=True)
class LevelDefinition:
    """Complete parameterization of one level: sprites, pacing, distance, speed."""

    name: str
    background: str
    distance: float
    start_speed: float
    max_speed: float
    entities: tuple[EntityDefinition, ...]


def _positive_number(value) -> bool:
    """Return True for int/float (not bool) values strictly greater than zero."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _label(index, entry) -> str:
    """Human label for a level entry in error messages, e.g. 'level 2 (desert)'."""
    name = entry.get("name") if isinstance(entry, dict) else None
    return f"level {index} ({name})" if isinstance(name, str) and name else f"level {index}"


def _check_sprite(entry, key, label, sprite_names, errors):
    """Validate entry[key] as a known sprite name; append a problem string on failure."""
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        errors.append(f"{label}: '{key}' must be a non-empty string")
    elif value not in sprite_names:
        errors.append(f"{label}: unknown sprite '{value}'")


def _check_number(entry, key, label, errors):
    """Validate entry[key] as a positive number; append a problem string on failure."""
    if not _positive_number(entry.get(key)):
        errors.append(f"{label}: '{key}' must be a positive number")


def _validate_entity(item, index, label, sprite_names, errors):
    """Validate one entry of the level's entities list; return it or None.

    All problems found for this item are appended to errors.
    """
    item_label = f"{label}: entities[{index}]"
    if not isinstance(item, dict):
        errors.append(f"{item_label}: must be a mapping")
        return None

    unknown = set(item) - _ENTITY_KEYS
    if unknown:
        errors.append(f"{item_label}: unknown key(s): {sorted(unknown)}")
    if not isinstance(item.get("type"), str) or not item.get("type"):
        errors.append(f"{item_label}: 'type' must be a non-empty string")
    _check_sprite(item, "sprite", item_label, sprite_names, errors)
    _check_number(item, "interval", item_label, errors)
    if "ramp_to" in item and not _positive_number(item["ramp_to"]):
        errors.append(f"{item_label}: 'ramp_to' must be a positive number")

    if any(e.startswith(item_label) for e in errors):
        return None
    ramp_to = item.get("ramp_to")
    return EntityDefinition(
        type=item["type"],
        sprite=item["sprite"],
        interval=item["interval"],
        ramp_to=ramp_to if ramp_to is not None else None,
    )


def _validate_entities(entry, label, sprite_names, errors):
    """Validate the level's entities list; return its definitions or None."""
    items = entry.get("entities")
    if not isinstance(items, list) or not items:
        errors.append(f"{label}: 'entities' must be a non-empty list")
        return None

    definitions = []
    for index, item in enumerate(items):
        definition = _validate_entity(item, index, label, sprite_names, errors)
        if definition is not None:
            definitions.append(definition)
    return tuple(definitions) if definitions else None


def _validate_level(index, entry, sprite_names, seen_names, errors):
    """Validate one level entry; return a LevelDefinition or None when invalid.

    All problems found for this entry are appended to errors (shared with
    other levels so one raise lists everything).
    """
    label = _label(index, entry)
    if not isinstance(entry, dict):
        errors.append(f"{label}: must be a mapping")
        return None

    unknown = set(entry) - _LEVEL_KEYS
    if unknown:
        errors.append(f"{label}: unknown key(s): {sorted(unknown)}")

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        errors.append(f"{label}: 'name' must be a non-empty string")
    elif name in seen_names:
        errors.append(f"{label}: duplicate name '{name}'")
    else:
        seen_names.add(name)

    _check_sprite(entry, "background", label, sprite_names, errors)
    for key in ("distance", "start_speed", "max_speed"):
        _check_number(entry, key, label, errors)

    entities = _validate_entities(entry, label, sprite_names, errors)

    if entities is None or any(e.startswith(label) for e in errors):
        return None
    return LevelDefinition(
        name=name,
        background=entry["background"],
        distance=entry["distance"],
        start_speed=entry["start_speed"],
        max_speed=entry["max_speed"],
        entities=entities,
    )


def load_levels(path: str, sprite_names: set[str]) -> list[LevelDefinition]:
    """Parse and validate levels.yaml; raise LevelConfigError listing all errors.

    sprite_names is the set of valid names from the sprite config, so
    unknown-sprite errors surface at load instead of at first spawn.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise LevelConfigError([f"file not found: {path}"]) from None
    except yaml.YAMLError as e:
        raise LevelConfigError([f"YAML parse error: {e}"]) from None

    if not isinstance(data, dict) or not isinstance(data.get("levels"), list) or not data["levels"]:
        raise LevelConfigError(["top level must be a mapping with a non-empty 'levels' list"])

    errors: list[str] = []
    seen_names: set[str] = set()
    levels: list[LevelDefinition] = []
    for index, entry in enumerate(data["levels"], start=1):
        definition = _validate_level(index, entry, sprite_names, seen_names, errors)
        if definition is not None:
            levels.append(definition)

    if errors:
        logger.error("Invalid level definitions:\n%s", "\n".join(errors))
        raise LevelConfigError(errors)
    return levels


def level_for(levels: list[LevelDefinition], number: int) -> LevelDefinition:
    """Return the level for a 1-based level number; repeat the last when beyond."""
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValueError(f"level number must be an integer >= 1, got {number!r}")
    return levels[min(number, len(levels)) - 1]
