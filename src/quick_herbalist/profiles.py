import copy
import logging
import os
import yaml

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manage game profiles, settings, and character data."""

    def __init__(self, config_dir=None):
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
            self._apply_default_config()
            self.save_config()
            return

        data = self._parse_config_file()
        if data is None:
            self._apply_default_config()
            self.save_config()
            return
        self._apply_loaded_data(data)

    def _parse_config_file(self):
        """Parse YAML config file. Re-raise all exceptions for caller handling."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError("Configuration data must be a dictionary.")
        except yaml.YAMLError as e:
            logger.error("YAML parse error in config file: %s", e)
            return None
        except PermissionError as e:
            logger.error("Permission denied reading config file: %s", e)
            raise
        except OSError as e:
            logger.error("OS error reading config file: %s", e)
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error("Unexpected error loading config: %s", e)
            raise

        return data

    def _apply_loaded_data(self, data):
        """Apply loaded configuration data to instance attributes."""
        self.active_character_name = data.get("active_character")

        loaded_settings = data.get("settings")
        if loaded_settings is None:
            loaded_settings = {}
        elif not isinstance(loaded_settings, dict):
            logger.warning(
                "Config 'settings' is corrupted (got %s), will raise error",
                type(loaded_settings).__name__,
            )
            raise ValueError(
                f"Config 'settings' must be a dict, got {type(loaded_settings).__name__}"
            )
        self.settings = copy.deepcopy(self.get_default_config()["settings"])
        self.settings.update(loaded_settings)

        loaded_characters = data.get("characters")
        if loaded_characters is None:
            loaded_characters = {}
        elif not isinstance(loaded_characters, dict):
            logger.warning(
                "Config 'characters' is corrupted (got %s), will raise error",
                type(loaded_characters).__name__,
            )
            raise ValueError(
                f"Config 'characters' must be a dict, got {type(loaded_characters).__name__}"
            )
        self.characters = copy.deepcopy(loaded_characters)

    def _apply_default_config(self):
        """Apply default configuration to instance attributes."""
        defaults = self.get_default_config()
        self.active_character_name = defaults["active_character"]
        # Deep-copy to avoid sharing mutable defaults
        self.settings = copy.deepcopy(defaults["settings"])
        self.characters = copy.deepcopy(defaults["characters"])

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
        if self.active_character_name and self.active_character_name in self.characters:
            return self.characters[self.active_character_name]
        return None

    def create_character(self, name):
        """Create new character with given name."""
        if not name or not isinstance(name, str):
            raise ValueError("Name cannot be empty.")
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("Name cannot be empty.")

        if stripped_name in self.characters:
            raise ValueError("Character already exists.")

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
            raise ValueError("Character not found.")
        self.active_character_name = name
        self.save_config()

    def complete_level(self):
        """Increment levels completed for active character."""
        if (
            not self.active_character_name
            or self.active_character_name not in self.characters
        ):
            raise ValueError("No active character selected.")

        char = self.characters[self.active_character_name]
        char["levels_completed"] = char.get("levels_completed", 0) + 1

        self.save_config()

    def add_flowers(self, flower_count):
        """Add flowers to active character inventory."""
        if (
            not self.active_character_name
            or self.active_character_name not in self.characters
        ):
            raise ValueError("No active character selected.")

        if not isinstance(flower_count, int) or isinstance(flower_count, bool):
            raise ValueError("flower_count must be an integer.")
        if flower_count <= 0:
            raise ValueError("flower_count must be a positive integer.")

        char = self.characters[self.active_character_name]
        if "inventory" not in char or not isinstance(char["inventory"], dict):
            char["inventory"] = {}
        char["inventory"]["flower"] = char["inventory"].get("flower", 0) + flower_count

        self.save_config()
