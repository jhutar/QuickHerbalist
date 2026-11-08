"""In-run flow screens: game view host, level completed, game over."""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from quick_herbalist.game.scene import GameView
from quick_herbalist.localization import _
from quick_herbalist.screens.base import KeyboardScreen, load_screen_kv


class GameScreen(KeyboardScreen):
    """Screen displaying the game view."""

    def on_enter(self):
        """Initialize the game view and start the run on entry."""
        super().on_enter()
        app = App.get_running_app()
        self.game_view = GameView(
            app.profile_manager,
            app.sprite_manager,
            app.levels,
            level_number=app.selected_level_number,
            recipes=app.recipes,
        )
        self.add_widget(self.game_view)
        self.game_view.start_game()

    def on_leave(self):
        """Stop the game and remove the game view on leave."""
        self.game_view.stop_game()
        self.remove_widget(self.game_view)
        super().on_leave()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for the game screen."""
        key = keycode[1]
        if key in ("escape", "q"):
            self.manager.current = "quit"
            return True
        return self.game_view.on_keyboard_down(key)

    def _on_keyboard_up(self, keyboard, keycode):
        """Handle keyboard key up events."""
        key = keycode[1]
        return self.game_view.on_keyboard_up(key)


class GameWonScreen(KeyboardScreen):
    """Screen shown when level is completed."""

    score = 0
    harvest = {}

    def on_pre_enter(self):
        """Initialize level completion UI."""
        self.ids.title.text = _("LEVEL COMPLETED!")
        self._render_harvest()
        self.ids.restart_btn.text = _("Next Level")
        self.ids.menu_btn.text = _("Game Menu")

    def _render_harvest(self):
        """Render one icon + name + count row per flower type collected this run."""
        app = App.get_running_app()
        box = self.ids.harvest_box
        box.clear_widgets()
        for sprite_name, count in self.harvest.items():
            row = BoxLayout(size_hint_y=0, spacing=10)
            sprite = app.sprite_manager.get(sprite_name)
            sprite.size_hint = (None, 1)
            sprite.size = (64, 64)
            row.add_widget(sprite)
            row.add_widget(
                Label(text=f"{_(sprite_name)}: {count}", font_size=28, color=(1, 1, 1, 1))
            )
            box.add_widget(row)

    def restart_game(self):
        """Start the level after the one just played, clamped at the last level."""
        app = App.get_running_app()
        app.selected_level_number = min(app.selected_level_number + 1, len(app.levels))
        self.manager.current = "game"

    def goto_menu(self):
        """Go to the game menu hub."""
        self.manager.current = "game_menu"


class GameOverScreen(KeyboardScreen):
    """Screen shown when player hits a stone."""

    score = 0
    distance = 0

    def on_pre_enter(self):
        """Initialize game over UI."""
        self.ids.title.text = _("GAME OVER!")
        self.ids.score_lbl.text = _("Collected: ") + str(self.score)
        self.ids.distance_lbl.text = _("Distance: ") + str(int(self.distance))
        self.ids.restart_btn.text = _("Play Again")
        self.ids.menu_btn.text = _("Game Menu")

    def on_back(self):
        """Quit the app from the game over screen."""
        App.get_running_app().stop()

    def restart_game(self):
        """Restart game."""
        self.manager.current = "game"

    def goto_menu(self):
        """Go to the game menu hub."""
        self.manager.current = "game_menu"


load_screen_kv("game_won.kv")
load_screen_kv("game_over.kv")
