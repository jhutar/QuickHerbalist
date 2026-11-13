import copy
import enum
import logging
import os

import yaml

from quick_herbalist.potions import RUN_SLOT_COUNT

logger = logging.getLogger(__name__)


class ProfileErrorCode(enum.StrEnum):
    """Machine codes for profile errors; safe to match on in consumers."""

    EMPTY_NAME = "EMPTY_NAME"
    DUPLICATE_CHARACTER = "DUPLICATE_CHARACTER"
    CHARACTER_NOT_FOUND = "CHARACTER_NOT_FOUND"
    NO_ACTIVE_CHARACTER = "NO_ACTIVE_CHARACTER"
    INVALID_FLOWER_COUNT = "INVALID_FLOWER_COUNT"
    INVALID_SPRITE_NAME = "INVALID_SPRITE_NAME"
    INVALID_POTION_ID = "INVALID_POTION_ID"
    NOT_ENOUGH_POTIONS = "NOT_ENOUGH_POTIONS"
    NO_FREE_RUN_SLOT = "NO_FREE_RUN_SLOT"
    INVALID_SLOT_INDEX = "INVALID_SLOT_INDEX"
    RUN_SLOT_TAKEN = "RUN_SLOT_TAKEN"
    RUN_SLOT_EMPTY = "RUN_SLOT_EMPTY"
    NOT_ENOUGH_FLOWERS = "NOT_ENOUGH_FLOWERS"
    NOT_IN_CAULDRON = "NOT_IN_CAULDRON"


class ProfileError(ValueError):
    """Domain error raised by ProfileManager; code is safe to match on."""

    def __init__(self, code: ProfileErrorCode, message: str):
        """Create a profile error with a machine code and a free human message."""
        super().__init__(message)
        self.code = code


class ProfileManager:
    """Manage game profiles, settings, and character data."""

    def __init__(self, config_dir=None):
        """Initialize ProfileManager with config directory and load configuration."""
        self.config_dir = self._resolve_config_dir(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, "config.yaml")
        self.active_character_name = None
        self.settings = {"fps": 60, "win_distance": 1000.0, "game_speed_start": 3.0}
        self.characters = {}
        self.load_config()

    def _resolve_config_dir(self, explicit_dir):
        """Resolve config directory from explicit path or platform defaults."""
        if explicit_dir:
            return explicit_dir

        from kivy.app import App

        app = App.get_running_app()
        return app.user_data_dir

    def get_default_config(self):
        """Return default configuration dictionary."""
        return {
            "active_character": None,
            "settings": {
                "fps": 60,
                "win_distance": 1000.0,
                "game_speed_start": 3.0,
                "locale": "system",
            },
            "characters": {},
        }

    def load_config(self):
        """Load configuration from file or apply defaults."""
        if not os.path.exists(self.config_path):
            logger.info("Configuration file does not exist")
            self._apply_default_config()
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.error("Configuration data must be a dictionary")
                    self._apply_default_config()
                    return
        except yaml.YAMLError as e:
            logger.error("YAML parse error in config file: %s", e)
            self._apply_default_config()
            return

        self._apply_loaded_data(data)

    def _apply_loaded_data(self, data):
        """Apply loaded configuration data to instance attributes.

        Missing or corrupted keys fall back to defaults.
        """
        self.active_character_name = data.get("active_character")

        self.settings = copy.deepcopy(self.get_default_config()["settings"])
        if isinstance(data.get("settings"), dict):
            self.settings.update(data.get("settings"))
        else:
            logger.error(
                f"Config 'settings' is corrupted (got {type(data.get('settings')).__name__})"
            )

        self.characters = copy.deepcopy(self.get_default_config()["characters"])
        if isinstance(data.get("characters"), dict):
            self.characters.update(data.get("characters"))
        else:
            logger.error(
                f"Config 'characters' is corrupted (got {type(data.get('characters')).__name__})"
            )
        self._migrate_characters()

    def _migrate_characters(self):
        """Ensure every character carries the potion, loadout and cauldron keys."""
        for char in self.characters.values():
            if not isinstance(char, dict):
                continue
            char.setdefault("potions", {})
            char.setdefault("cauldron", {})
            char.setdefault("seen_entities", [])
            char.setdefault("show_hints", True)
            loadout = char.get("run_loadout")
            if not isinstance(loadout, list):
                char["run_loadout"] = [None] * RUN_SLOT_COUNT
                continue
            while len(char["run_loadout"]) < RUN_SLOT_COUNT:
                char["run_loadout"].append(None)
            char["run_loadout"] = char["run_loadout"][:RUN_SLOT_COUNT]

    def _apply_default_config(self):
        """Apply default configuration to instance attributes."""
        defaults = self.get_default_config()
        self.active_character_name = defaults["active_character"]
        # Deep-copy to avoid sharing mutable defaults
        self.settings = copy.deepcopy(defaults["settings"])
        self.characters = copy.deepcopy(defaults["characters"])

        self.save_config()

    def save_config(self):
        """Save configuration to YAML file."""
        data = {
            "active_character": self.active_character_name,
            "settings": self.settings,
            "characters": self.characters,
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    @property
    def active_character(self):
        """Get currently active character or None."""
        return self.characters.get(self.active_character_name)

    def create_character(self, name, show_hints=True):
        """Create new character with given name; hints enabled unless show_hints is False."""
        if not name or not isinstance(name, str):
            raise ProfileError(ProfileErrorCode.EMPTY_NAME, "Name cannot be empty.")

        stripped_name = name.strip()
        if not stripped_name:
            raise ProfileError(ProfileErrorCode.EMPTY_NAME, "Name cannot be empty.")

        if stripped_name in self.characters:
            raise ProfileError(ProfileErrorCode.DUPLICATE_CHARACTER, "Character already exists.")

        self.characters[stripped_name] = {
            "name": stripped_name,
            "levels_completed": 0,
            "inventory": {},
            "potions": {},
            "run_loadout": [None] * RUN_SLOT_COUNT,
            "cauldron": {},
            "seen_entities": [],
            "show_hints": bool(show_hints),
        }

        self.active_character_name = stripped_name
        self.save_config()

    def select_character(self, name):
        """Select existing character by name."""
        if not name or name not in self.characters:
            raise ProfileError(ProfileErrorCode.CHARACTER_NOT_FOUND, "Character not found.")

        self.active_character_name = name
        self.save_config()

    def hints_enabled(self):
        """Return whether in-run tutorial hints are enabled for the active character."""
        char = self.active_character
        if char is None:
            return True
        return bool(char.get("show_hints", True))

    def get_seen_entities(self):
        """Return the list of entity types whose hint the active character was shown."""
        char = self.active_character
        if char is None:
            return []
        return list(char.get("seen_entities", []))

    def mark_entity_seen(self, entity_type):
        """Record that the active character was shown the hint for entity_type."""
        char = self.active_character
        if char is None:
            return
        seen = char.setdefault("seen_entities", [])
        if entity_type not in seen:
            seen.append(entity_type)
            self.save_config()

    def next_level_number(self):
        """Return the 1-based level number the active character plays next."""
        char = self.active_character
        if not char:
            return 1
        return char.get("levels_completed", 0) + 1

    def playable_level_numbers(self, max_levels=None):
        """Return 1-based level numbers the active character may start playing.

        Includes all completed levels plus the next one, capped at max_levels.
        """
        next_level = self.next_level_number()
        if max_levels is not None:
            next_level = min(next_level, max_levels)
        return list(range(1, next_level + 1))

    def complete_level(self):
        """Increment levels completed for active character."""
        if not self.active_character_name or self.active_character_name not in self.characters:
            raise ProfileError(
                ProfileErrorCode.NO_ACTIVE_CHARACTER, "No active character selected."
            )

        char = self.characters[self.active_character_name]
        char["levels_completed"] = char.get("levels_completed", 0) + 1
        self.save_config()

    def add_flowers(self, sprite_name, flower_count):
        """Add flowers of the given type (sprite key) to the active character inventory."""
        if not self.active_character_name or self.active_character_name not in self.characters:
            raise ProfileError(
                ProfileErrorCode.NO_ACTIVE_CHARACTER, "No active character selected."
            )

        if not isinstance(sprite_name, str) or not sprite_name:
            raise ProfileError(
                ProfileErrorCode.INVALID_SPRITE_NAME,
                "sprite_name must be a non-empty string.",
            )
        if not isinstance(flower_count, int) or isinstance(flower_count, bool):
            raise ProfileError(
                ProfileErrorCode.INVALID_FLOWER_COUNT,
                "flower_count must be an integer.",
            )
        if flower_count < 0:
            raise ProfileError(
                ProfileErrorCode.INVALID_FLOWER_COUNT,
                "flower_count must be a non-negative integer.",
            )

        char = self.characters[self.active_character_name]
        if "inventory" not in char or not isinstance(char["inventory"], dict):
            char["inventory"] = {}
        char["inventory"][sprite_name] = char["inventory"].get(sprite_name, 0) + flower_count

        self.save_config()

    def _require_active(self):
        """Raise ProfileError when there is no active character to mutate."""
        if not self.active_character_name or self.active_character_name not in self.characters:
            raise ProfileError(
                ProfileErrorCode.NO_ACTIVE_CHARACTER, "No active character selected."
            )

    def _validate_potion_id(self, potion_id):
        """Raise ProfileError when potion_id is not a non-empty string."""
        if not isinstance(potion_id, str) or not potion_id:
            raise ProfileError(
                ProfileErrorCode.INVALID_POTION_ID,
                "potion_id must be a non-empty string.",
            )

    def get_inventory(self):
        """Return the active character's flower inventory as a dict."""
        char = self.active_character
        if char is None:
            return {}
        return char.get("inventory", {})

    def get_potions(self):
        """Return the active character's brewed potion counts as a dict."""
        char = self.active_character
        if char is None:
            return {}
        return char.get("potions", {})

    def get_potion_count(self, potion_id):
        """Return how many of the given potion the active character holds."""
        return self.get_potions().get(potion_id, 0)

    def add_potion(self, potion_id, count=1):
        """Add brewed potions of the given type to the active character inventory."""
        self._require_active()
        self._validate_potion_id(potion_id)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ProfileError(
                ProfileErrorCode.NOT_ENOUGH_POTIONS, "count must be a positive integer."
            )
        potions = self.characters[self.active_character_name].setdefault("potions", {})
        potions[potion_id] = potions.get(potion_id, 0) + count
        self.save_config()

    def consume_potion(self, potion_id, count=1):
        """Remove potions of the given type; fail fast when not enough are held."""
        self._require_active()
        self._validate_potion_id(potion_id)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ProfileError(
                ProfileErrorCode.NOT_ENOUGH_POTIONS, "count must be a positive integer."
            )
        char = self.characters[self.active_character_name]
        potions = char.setdefault("potions", {})
        if potions.get(potion_id, 0) < count:
            raise ProfileError(
                ProfileErrorCode.NOT_ENOUGH_POTIONS,
                f"Not enough '{potion_id}' potions.",
            )
        potions[potion_id] -= count
        if potions[potion_id] == 0:
            del potions[potion_id]
        self.save_config()

    def get_cauldron(self):
        """Return the active character's cauldron contents as a dict."""
        char = self.active_character
        if char is None:
            return {}
        return char.get("cauldron", {})

    def move_flower_to_cauldron(self, sprite_name):
        """Move one flower unit from the inventory into the cauldron."""
        self._require_active()
        if not isinstance(sprite_name, str) or not sprite_name:
            raise ProfileError(
                ProfileErrorCode.INVALID_SPRITE_NAME,
                "sprite_name must be a non-empty string.",
            )
        char = self.characters[self.active_character_name]
        inventory = char.setdefault("inventory", {})
        if inventory.get(sprite_name, 0) < 1:
            raise ProfileError(
                ProfileErrorCode.NOT_ENOUGH_FLOWERS,
                f"Not enough '{sprite_name}' in inventory.",
            )
        inventory[sprite_name] -= 1
        if inventory[sprite_name] == 0:
            del inventory[sprite_name]
        cauldron = char.setdefault("cauldron", {})
        cauldron[sprite_name] = cauldron.get(sprite_name, 0) + 1
        self.save_config()

    def move_cauldron_ingredient_to_inventory(self, sprite_name):
        """Move one ingredient unit from the cauldron back to the inventory."""
        self._require_active()
        if not isinstance(sprite_name, str) or not sprite_name:
            raise ProfileError(
                ProfileErrorCode.INVALID_SPRITE_NAME,
                "sprite_name must be a non-empty string.",
            )
        char = self.characters[self.active_character_name]
        cauldron = char.setdefault("cauldron", {})
        if cauldron.get(sprite_name, 0) < 1:
            raise ProfileError(
                ProfileErrorCode.NOT_IN_CAULDRON,
                f"'{sprite_name}' is not in the cauldron.",
            )
        cauldron[sprite_name] -= 1
        if cauldron[sprite_name] == 0:
            del cauldron[sprite_name]
        inventory = char.setdefault("inventory", {})
        inventory[sprite_name] = inventory.get(sprite_name, 0) + 1
        self.save_config()

    def clear_cauldron(self):
        """Empty the cauldron; its ingredients are lost forever."""
        self._require_active()
        self.characters[self.active_character_name]["cauldron"] = {}
        self.save_config()

    def get_run_loadout(self):
        """Return the RUN_SLOT_COUNT-slot next-run loadout as a list of potion ids or None."""
        char = self.active_character
        if char is None:
            return [None] * RUN_SLOT_COUNT
        loadout = char.get("run_loadout")
        if not isinstance(loadout, list):
            return [None] * RUN_SLOT_COUNT
        return list(loadout[:RUN_SLOT_COUNT]) + [None] * (
            RUN_SLOT_COUNT - len(loadout[:RUN_SLOT_COUNT])
        )

    def _ensure_loadout(self):
        """Return the active character's loadout list, padded or trimmed to RUN_SLOT_COUNT."""
        char = self.characters[self.active_character_name]
        loadout = char.get("run_loadout")
        if not isinstance(loadout, list):
            char["run_loadout"] = [None] * RUN_SLOT_COUNT
        else:
            while len(char["run_loadout"]) < RUN_SLOT_COUNT:
                char["run_loadout"].append(None)
            char["run_loadout"] = char["run_loadout"][:RUN_SLOT_COUNT]
        return char["run_loadout"]

    def _validate_slot_index(self, slot_index):
        """Raise ProfileError when slot_index is not an int in range."""
        if (
            not isinstance(slot_index, int)
            or isinstance(slot_index, bool)
            or not 0 <= slot_index < RUN_SLOT_COUNT
        ):
            raise ProfileError(
                ProfileErrorCode.INVALID_SLOT_INDEX,
                f"slot_index must be an integer in 0..{RUN_SLOT_COUNT - 1}.",
            )

    def assign_potion_to_slot(self, potion_id, slot_index=None):
        """Move one potion from the inventory into a run slot.

        With slot_index None the first free slot is used; otherwise the given
        slot must be empty. Fails fast when no slot is free or the potion is
        missing.
        """
        self._require_active()
        self._validate_potion_id(potion_id)
        loadout = self._ensure_loadout()
        if slot_index is None:
            if None not in loadout:
                raise ProfileError(ProfileErrorCode.NO_FREE_RUN_SLOT, "All run slots are taken.")
            slot_index = loadout.index(None)
        else:
            self._validate_slot_index(slot_index)
            if loadout[slot_index] is not None:
                raise ProfileError(
                    ProfileErrorCode.RUN_SLOT_TAKEN, f"Run slot {slot_index} is already taken."
                )
        self.consume_potion(potion_id)
        loadout[slot_index] = potion_id
        self.save_config()

    def release_run_slot(self, slot_index):
        """Return the potion from a run slot back to the potions inventory."""
        self._require_active()
        self._validate_slot_index(slot_index)
        loadout = self._ensure_loadout()
        if loadout[slot_index] is None:
            raise ProfileError(ProfileErrorCode.RUN_SLOT_EMPTY, f"Run slot {slot_index} is empty.")
        self.add_potion(loadout[slot_index])
        loadout[slot_index] = None
        self.save_config()

    def use_run_slot(self, slot_index):
        """Consume the potion in a run slot; it is lost and not returned to inventory."""
        self._require_active()
        self._validate_slot_index(slot_index)
        loadout = self._ensure_loadout()
        if loadout[slot_index] is None:
            raise ProfileError(ProfileErrorCode.RUN_SLOT_EMPTY, f"Run slot {slot_index} is empty.")
        loadout[slot_index] = None
        self.save_config()
