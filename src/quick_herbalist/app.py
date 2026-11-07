"""Application entry: window config, App class, and main()."""

import logging

# Kivy setup (force window size before other imports)
from kivy.config import Config

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "600")
Config.set("graphics", "resizable", "0")

from kivy.app import App  # noqa: E402
from kivy.uix.screenmanager import ScreenManager  # noqa: E402

from quick_herbalist.core.config_parser import get_asset_path  # noqa: E402
from quick_herbalist.core.level_config import LevelConfigError, load_levels  # noqa: E402
from quick_herbalist.core.sprite_manager import SpriteManager  # noqa: E402
from quick_herbalist.profiles import ProfileManager  # noqa: E402
from quick_herbalist.screens import (  # noqa: E402
    GameOverScreen,
    GameScreen,
    GameWonScreen,
    LoadCharacterScreen,
    MenuScreen,
    NewCharacterScreen,
    PotionsScreen,
    QuitScreen,
)


class QuickHerbalistApp(App):
    """Main application for Quick Herbalist game."""

    def build(self):
        """Build the app with screen manager and all screens."""
        logger = logging.getLogger(__name__)
        self.profile_manager = ProfileManager()
        self.sprite_manager = SpriteManager()
        try:
            self.levels = load_levels(get_asset_path("levels.yaml"), self.sprite_manager.names())
        except LevelConfigError as e:
            logger.error("Refusing to start, invalid level definitions:\n%s", e)
            raise SystemExit(str(e)) from e

        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(NewCharacterScreen(name="new_character"))
        sm.add_widget(LoadCharacterScreen(name="load_character"))
        sm.add_widget(PotionsScreen(name="potions"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(GameWonScreen(name="game_won"))
        sm.add_widget(QuitScreen(name="quit"))
        sm.add_widget(GameOverScreen(name="game_over"))

        # Skip main menu and redirect directly to "new_character" if no active character exists
        if self.profile_manager.active_character_name is None:
            sm.current = "new_character"
        else:
            sm.current = "menu"

        return sm


def main():
    """Entry point: run the Quick Herbalist app."""
    QuickHerbalistApp().run()


if __name__ == "__main__":
    main()
