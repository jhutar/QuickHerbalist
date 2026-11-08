"""Main menu, game menu hub, character management, and quit screens."""

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from quick_herbalist.localization import _
from quick_herbalist.profiles import ProfileError, ProfileErrorCode
from quick_herbalist.screens.base import KeyboardScreen, load_screen_kv


class MenuScreen(KeyboardScreen):
    """Main menu screen."""

    def on_pre_enter(self):
        """Initialize menu labels and buttons before entering."""
        app = App.get_running_app()
        self.ids.title.text = _("Quick Herbalist")
        self.ids.subtitle.text = _("Press 's' to start")
        active_name = app.profile_manager.active_character_name
        self.ids.active_char_lbl.text = _("Active Character: ") + (
            active_name if active_name else _("None")
        )
        self.ids.start_btn.text = _("Start Game")
        self.ids.new_btn.text = _("New Character")
        self.ids.load_btn.text = _("Load Character")
        self.ids.quit_btn.text = _("Quit")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle menu keyboard shortcuts."""
        key = keycode[1]
        if key == "s":
            self.start_game()
            return True
        elif key == "n":
            self.manager.current = "new_character"
            return True
        elif key == "l":
            self.manager.current = "load_character"
            return True
        return super()._on_keyboard_down(keyboard, keycode, text, modifiers)

    def on_back(self):
        """Quit the app when leaving the main menu."""
        App.get_running_app().stop()

    def start_game(self):
        """Switch to the game menu hub."""
        self.manager.current = "game_menu"


class GameMenuScreen(KeyboardScreen):
    """Hub screen for starting a run and accessing secondary systems."""

    def on_pre_enter(self):
        """Initialize game menu labels and buttons before entering."""
        self.ids.title.text = _("Game Menu")
        self._build_level_buttons()
        self.ids.potions_btn.text = _("Create Potions")
        self.ids.greenhouse_btn.text = _("Greenhouse")
        self.ids.back_btn.text = _("Back to Main Menu")

    def _build_level_buttons(self):
        """Build one Start Level button per playable level."""
        app = App.get_running_app()
        numbers = app.profile_manager.playable_level_numbers(max_levels=len(app.levels))
        layout = self.ids.level_buttons
        layout.clear_widgets()
        for number in numbers:
            btn = Button(
                text=_("Start Level ") + str(number),
                size_hint_y=None,
                height=50,
                font_size=18,
            )
            btn.bind(on_release=lambda _btn, n=number: self.start_level(n))
            layout.add_widget(btn)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle game menu keyboard shortcuts."""
        key = keycode[1]
        if key == "s":
            self.start_run()
            return True
        elif key == "c":
            self.manager.current = "potions"
            return True
        elif key == "g":
            self.manager.current = "greenhouse"
            return True
        return super()._on_keyboard_down(keyboard, keycode, text, modifiers)

    def start_level(self, level_number):
        """Start a run at the given level number."""
        App.get_running_app().selected_level_number = level_number
        self.manager.current = "game"

    def start_run(self):
        """Start a run at the next available level."""
        app = App.get_running_app()
        app.selected_level_number = app.profile_manager.next_level_number()
        self.manager.current = "game"


class NewCharacterScreen(Screen):
    """Screen for creating a new character."""

    def on_pre_enter(self):
        """Initialize character creation UI."""
        self.ids.title.text = _("Enter Character Name")
        self.ids.name_input.text = ""
        self.ids.error_label.text = ""
        self.ids.confirm_btn.text = _("Confirm")

        app = App.get_running_app()
        if app.profile_manager.active_character_name is None:
            self.ids.back_btn.opacity = 0
            self.ids.back_btn.disabled = True
            self.ids.back_btn.text = ""
        else:
            self.ids.back_btn.opacity = 1
            self.ids.back_btn.disabled = False
            self.ids.back_btn.text = _("Back to Menu")

    def confirm(self):
        """Create new character with input name."""
        app = App.get_running_app()
        name = self.ids.name_input.text
        try:
            app.profile_manager.create_character(name)
            self.manager.current = "menu"
        except ProfileError as e:
            messages = {
                ProfileErrorCode.EMPTY_NAME: _("Name cannot be empty."),
                ProfileErrorCode.DUPLICATE_CHARACTER: _("Character already exists."),
            }
            self.ids.error_label.text = messages.get(e.code, _(str(e)))

    def back_to_menu(self):
        """Return to main menu."""
        self.manager.current = "menu"


class LoadCharacterScreen(KeyboardScreen):
    """Screen for loading existing characters."""

    def on_pre_enter(self):
        """Populate character list before entering."""
        self.ids.title.text = _("Select Character")
        self.ids.back_btn.text = _("Back to Menu")

        self.ids.list_layout.clear_widgets()

        app = App.get_running_app()
        for name in app.profile_manager.characters.keys():
            btn = Button(text=name, size_hint_y=None, height=50, font_size=18)
            btn.bind(on_release=self.select_and_return)
            self.ids.list_layout.add_widget(btn)

    def select_and_return(self, btn):
        """Select character and return to menu."""
        app = App.get_running_app()
        app.profile_manager.select_character(btn.text)
        self.manager.current = "menu"

    def back_to_menu(self):
        """Return to main menu."""
        self.manager.current = "menu"


class QuitScreen(KeyboardScreen):
    """Screen asking user if they want to quit."""

    def on_pre_enter(self):
        """Initialize quit confirmation UI."""
        self.ids.title.text = _("Do you want to quit?")
        self.ids.cont_lbl.text = _("Press 's' to continue")
        self.ids.quit_lbl.text = _("Press 'q' to quit")
        self.ids.resume_btn.text = _("Continue")
        self.ids.quit_btn.text = _("Quit")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle 's' to resume the game; leave escape/q to the base class."""
        if keycode[1] == "s":
            self.resume_game()
            return True
        return super()._on_keyboard_down(keyboard, keycode, text, modifiers)

    def on_back(self):
        """Quit the app from the quit screen."""
        App.get_running_app().stop()

    def resume_game(self):
        """Return to game."""
        self.manager.current = "game"


load_screen_kv("menu.kv")
load_screen_kv("game_menu.kv")
load_screen_kv("new_character.kv")
load_screen_kv("load_character.kv")
load_screen_kv("quit.kv")
