import os
import yaml


class ProfileManager:
    def __init__(self, config_dir=None):
        if config_dir:
            self.config_dir = config_dir
        else:
            # Attempt to resolve from running Kivy App
            try:
                from kivy.app import App

                kivy_app = App.get_running_app()
                if kivy_app and kivy_app.user_data_dir:
                    self.config_dir = kivy_app.user_data_dir
                else:
                    self.config_dir = self._get_fallback_config_dir()
            except Exception:
                self.config_dir = self._get_fallback_config_dir()

        # Ensure directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, "config.yaml")

        self.active_character_name = None
        self.settings = {"fps": 60, "win_distance": 1000.0, "game_speed_start": 3.0}
        self.characters = {}

        # Load configuration on initialization
        self.load_config()

    def _get_fallback_config_dir(self):
        # Resolve standard OS-specific config directory
        home = os.path.expanduser("~")
        if os.name == "nt":  # Windows
            appdata = os.environ.get(
                "APPDATA", os.path.join(home, "AppData", "Roaming")
            )
            return os.path.join(appdata, "quickherbalist")
        elif os.name == "posix":  # macOS / Linux
            # Follow XDG on Linux, default to Library on macOS if preferred,
            # but simple ~/.config/quickherbalist or ~/.quickherbalist is highly standard.
            if os.uname().sysname == "Darwin":
                return os.path.join(
                    home, "Library", "Application Support", "quickherbalist"
                )
            else:
                return os.path.join(home, ".config", "quickherbalist")
        else:
            return os.path.join(home, ".quickherbalist")

    def get_default_config(self):
        return {
            "active_character": None,
            "settings": {"fps": 60, "win_distance": 1000.0, "game_speed_start": 3.0},
            "characters": {},
        }

    def load_config(self):
        if not os.path.exists(self.config_path):
            self._apply_default_config()
            self.save_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError("Configuration data must be a dictionary.")
        except Exception:
            # File is corrupted or parsing failed, fallback to defaults
            self._apply_default_config()
            self.save_config()
            return

        # Safe extraction of data with robust defaults
        self.active_character_name = data.get("active_character")

        # Merge settings with default to handle missing fields gracefully
        loaded_settings = data.get("settings", {})
        if not isinstance(loaded_settings, dict):
            loaded_settings = {}
        for key, val in self.get_default_config()["settings"].items():
            self.settings[key] = loaded_settings.get(key, val)

        # Retrieve characters
        self.characters = data.get("characters", {})
        if not isinstance(self.characters, dict):
            self.characters = {}

    def _apply_default_config(self):
        defaults = self.get_default_config()
        self.active_character_name = defaults["active_character"]
        self.settings = defaults["settings"]
        self.characters = defaults["characters"]

    def save_config(self):
        data = {
            "active_character": self.active_character_name,
            "settings": self.settings,
            "characters": self.characters,
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    @property
    def active_character(self):
        if self.active_character_name and self.active_character_name in self.characters:
            return self.characters[self.active_character_name]
        return None

    def create_character(self, name):
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
        if not name or name not in self.characters:
            raise ValueError("Character not found.")
        self.active_character_name = name
        self.save_config()

    def add_rewards(self, flower_count):
        if (
            not self.active_character_name
            or self.active_character_name not in self.characters
        ):
            raise ValueError("No active character selected.")

        char = self.characters[self.active_character_name]
        char["levels_completed"] = char.get("levels_completed", 0) + 1

        if "inventory" not in char or not isinstance(char["inventory"], dict):
            char["inventory"] = {}
        char["inventory"]["flower"] = char["inventory"].get("flower", 0) + flower_count

        self.save_config()
