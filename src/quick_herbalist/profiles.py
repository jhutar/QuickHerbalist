import copy
import enum
import logging
import os

import yaml

logger = logging.getLogger(__name__)


class ProfileErrorCode(enum.StrEnum):
    """Machine codes for profile errors; safe to match on in consumers."""

    EMPTY_NAME = "EMPTY_NAME"
    DUPLICATE_CHARACTER = "DUPLICATE_CHARACTER"
    CHARACTER_NOT_FOUND = "CHARACTER_NOT_FOUND"
    NO_ACTIVE_CHARACTER = "NO_ACTIVE_CHARACTER"
    INVALID_FLOWER_COUNT = "INVALID_FLOWER_COUNT"


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
            "settings": {"fps": 60, "win_distance": 1000.0, "game_speed_start": 3.0},
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

    def create_character(self, name):
        """Create new character with given name."""
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
            "inventory": {"flower": 0},
        }

        self.active_character_name = stripped_name
        self.save_config()

    def select_character(self, name):
        """Select existing character by name."""
        if not name or name not in self.characters:
            raise ProfileError(ProfileErrorCode.CHARACTER_NOT_FOUND, "Character not found.")

        self.active_character_name = name
        self.save_config()

    def next_level_number(self):
        """Return the 1-based level number the active character plays next."""
        char = self.active_character
        if not char:
            return 1
        return char.get("levels_completed", 0) + 1

    def complete_level(self):
        """Increment levels completed for active character."""
        if not self.active_character_name or self.active_character_name not in self.characters:
            raise ProfileError(
                ProfileErrorCode.NO_ACTIVE_CHARACTER, "No active character selected."
            )

        char = self.characters[self.active_character_name]
        char["levels_completed"] = char.get("levels_completed", 0) + 1
        self.save_config()

    def add_flowers(self, flower_count):
        """Add flowers to active character inventory."""
        if not self.active_character_name or self.active_character_name not in self.characters:
            raise ProfileError(
                ProfileErrorCode.NO_ACTIVE_CHARACTER, "No active character selected."
            )

        if not isinstance(flower_count, int) or isinstance(flower_count, bool):
            raise ProfileError(
                ProfileErrorCode.INVALID_FLOWER_COUNT,
                "flower_count must be an integer.",
            )
        if flower_count <= 0:
            raise ProfileError(
                ProfileErrorCode.INVALID_FLOWER_COUNT,
                "flower_count must be a positive integer.",
            )

        char = self.characters[self.active_character_name]
        if "inventory" not in char or not isinstance(char["inventory"], dict):
            char["inventory"] = {}
        char["inventory"]["flower"] = char["inventory"].get("flower", 0) + flower_count

        self.save_config()
