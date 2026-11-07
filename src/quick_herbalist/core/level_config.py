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

_LEVEL_KEYS = {"name", "background", "distance", "start_speed", "max_speed", "flower", "stone"}
_FLOWER_KEYS = {"sprite", "interval"}
_STONE_KEYS = {"sprite", "interval", "ramp_to"}


class LevelConfigError(ValueError):
    """Raised when levels.yaml fails validation; message lists all errors."""

    def __init__(self, errors: list[str]):
        """Create the error from a list of human-readable problem strings."""
        super().__init__("levels.yaml invalid:\n" + "\n".join(f"  - {e}" for e in errors))
        self.errors = errors


@dataclass(frozen=True)
class SpawnDefinition:
    """One spawnable entity type: which sprite, at what interval (seconds)."""

    sprite: str
    interval: float


@dataclass(frozen=True)
class StoneDefinition(SpawnDefinition):
    """Stone spawn definition with optional in-level ramp (minimum interval).

    ramp_to None means the interval stays constant for the whole level.
    """

    ramp_to: float | None = None


@dataclass(frozen=True)
class LevelDefinition:
    """Complete parameterization of one level: sprites, pacing, distance, speed."""

    name: str
    background: str
    distance: float
    start_speed: float
    max_speed: float
    flower: SpawnDefinition
    stone: StoneDefinition


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


def _validate_spawn(entry, key, allowed_keys, label, sprite_names, errors):
    """Validate a spawn sub-mapping (flower/stone); return its values or None.

    Appends all problems found for this sub-mapping to errors.
    """
    sub = entry.get(key)
    if not isinstance(sub, dict):
        errors.append(f"{label}: '{key}' must be a mapping")
        return None
    unknown = set(sub) - allowed_keys
    if unknown:
        errors.append(f"{label}: {key}: unknown key(s): {sorted(unknown)}")
    if not isinstance(sub.get("sprite"), str) or not sub.get("sprite"):
        errors.append(f"{label}: {key}.sprite must be a non-empty string")
    elif sub["sprite"] not in sprite_names:
        errors.append(f"{label}: {key}: unknown sprite '{sub['sprite']}'")
    if not _positive_number(sub.get("interval")):
        errors.append(f"{label}: {key}.interval must be a positive number")
        return None
    return sub["sprite"], sub["interval"]


def _validate_level(index, entry, sprite_names, seen_names, errors):
    """Validate one level entry; return a LevelDefinition or None when invalid.

    All problems found for this entry are appended to errors (shared with
    other levels so one raise lists everything).
    """
    label = _label(index, entry)
    local_errors: list[str] = []
    if not isinstance(entry, dict):
        errors.append(f"{label}: must be a mapping")
        return None

    unknown = set(entry) - _LEVEL_KEYS
    if unknown:
        local_errors.append(f"{label}: unknown key(s): {sorted(unknown)}")

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        errors.append(f"{label}: 'name' must be a non-empty string")
    elif name in seen_names:
        errors.append(f"{label}: duplicate name '{name}'")
    else:
        seen_names.add(name)

    _check_sprite(entry, "background", label, sprite_names, local_errors)
    for key in ("distance", "start_speed", "max_speed"):
        _check_number(entry, key, label, local_errors)

    flower = _validate_spawn(entry, "flower", _FLOWER_KEYS, label, sprite_names, local_errors)
    stone = _validate_spawn(entry, "stone", _STONE_KEYS, label, sprite_names, local_errors)

    ramp_to = None
    if stone is not None and entry["stone"].get("ramp_to") is not None:
        if not _positive_number(entry["stone"]["ramp_to"]):
            local_errors.append(f"{label}: stone.ramp_to must be a positive number")
            flower = stone = None
        else:
            ramp_to = entry["stone"]["ramp_to"]

    errors.extend(local_errors)
    if flower is None or stone is None or local_errors:
        return None
    return LevelDefinition(
        name=name,
        background=entry["background"],
        distance=entry["distance"],
        start_speed=entry["start_speed"],
        max_speed=entry["max_speed"],
        flower=SpawnDefinition(*flower),
        stone=StoneDefinition(sprite=stone[0], interval=stone[1], ramp_to=ramp_to),
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
