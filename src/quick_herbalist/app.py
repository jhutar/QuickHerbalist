"""Application entry: window config, App class, and main()."""

# Kivy setup (force window size before other imports)
from kivy.config import Config

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "600")
Config.set("graphics", "resizable", "0")

from kivy.app import App  # noqa: E402
from kivy.uix.screenmanager import ScreenManager  # noqa: E402

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
        self.profile_manager = ProfileManager()
        self.sprite_manager = SpriteManager()

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
