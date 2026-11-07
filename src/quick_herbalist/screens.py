"""All menu/flow screens plus their KV definitions."""

import logging

from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from quick_herbalist.core.config_parser import get_asset_path
from quick_herbalist.game_scene import GameView
from quick_herbalist.localization import _
from quick_herbalist.potions import match_recipe
from quick_herbalist.profiles import ProfileError, ProfileErrorCode

logger = logging.getLogger(__name__)


class KeyboardScreen(Screen):
    """Base screen class with keyboard support."""

    def on_enter(self):
        """Handle screen entry and request keyboard."""
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def on_leave(self):
        """Handle screen exit and unbind keyboard."""
        if self._keyboard:
            self._keyboard.unbind(
                on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
            )
            self._keyboard = None

    def _keyboard_closed(self):
        """Callback when keyboard is closed."""
        self._keyboard = None

    def on_back(self):
        """Default back behaviour: return to the main menu."""
        self.manager.current = "menu"

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle escape/q as back; return True when the key was handled."""
        if keycode[1] in ("escape", "q"):
            self.on_back()
            return True
        return False

    def _on_keyboard_up(self, keyboard, keycode):
        """Handle key up event."""
        return False


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


class GameWonScreen(KeyboardScreen):
    """Screen shown when level is completed."""

    score = 0
    harvest = {}

    def on_pre_enter(self):
        """Initialize level completion UI."""
        self.ids.title.text = _("LEVEL COMPLETED!")
        self._render_harvest()
        self.ids.restart_btn.text = _("Next Level")
        self.ids.menu_btn.text = _("Main Menu")

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


class Draggable(FloatLayout):
    """Base widget that can be dragged onto a drop target, with click support.

    Set drop_target, drop_handler, click_handler and drag_image_source before
    use. A drop fires when the touch ends over drop_target after a real move;
    a click fires when the touch ends on the widget without moving.
    """

    def __init__(self, **kwargs):
        """Initialize drag state and handlers."""
        super().__init__(**kwargs)
        self.drop_target = None
        self.drop_handler = None
        self.click_handler = None
        self.drag_image_source = None

    def on_touch_down(self, touch):
        """Start a drag when the touch lands on this widget."""
        if self.collide_point(*touch.pos):
            touch.ud["qh_drag"] = self
            touch.ud["qh_moved"] = False
            if self.drag_image_source is not None:
                proxy = Image(source=self.drag_image_source)
                proxy.size = (48, 48)
                proxy.center = (touch.x, touch.y)
                self.get_root_window().add_widget(proxy)
                touch.ud["qh_proxy"] = proxy
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """Move the drag proxy while the touch is held."""
        if touch.ud.get("qh_drag") is self:
            if abs(touch.x - touch.sx) + abs(touch.y - touch.sy) > 15:
                touch.ud["qh_moved"] = True
            if "qh_proxy" in touch.ud:
                touch.ud["qh_proxy"].center = (touch.x, touch.y)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Finish the drag: commit a drop, fire a click, or cancel silently."""
        if touch.ud.get("qh_drag") is self:
            moved = touch.ud.pop("qh_moved", False)
            touch.ud.pop("qh_drag")
            proxy = touch.ud.pop("qh_proxy", None)
            if proxy is not None:
                self.get_root_window().remove_widget(proxy)
            if (
                moved
                and self.drop_target is not None
                and self.drop_target.collide_point(*touch.pos)
            ):
                if self.drop_handler is not None:
                    self.drop_handler(touch)
            elif not moved and self.click_handler is not None:
                self.click_handler()
            return True
        return super().on_touch_up(touch)


# KV rules resolve widget names through the Factory only
Factory.register("Draggable", cls=Draggable)


class CauldronSlot(FloatLayout):
    """One 2x2 grid cell over the cauldron showing a held ingredient."""

    def __init__(self, remove_handler=None, **kwargs):
        """Create an empty cauldron cell."""
        super().__init__(**kwargs)
        self.remove_handler = remove_handler
        self.sprite_name = None
        self.opacity = 0

    def set_ingredient(self, sprite_name, count, sprite_widget):
        """Show one ingredient with a count badge in the lower right corner."""
        self.sprite_name = sprite_name
        self.opacity = 1
        self.clear_widgets()
        sprite_widget.size = (60, 60)
        sprite_widget.pos_hint = {"center_x": 0.42, "center_y": 0.55}
        self.add_widget(sprite_widget)
        badge = Label(text=str(count), font_size=20, color=(1, 1, 0, 1))
        badge.pos_hint = {"x": 0.65, "y": 0}
        self.add_widget(badge)

    def clear_slot(self):
        """Empty this cell and hide it."""
        self.sprite_name = None
        self.opacity = 0
        self.clear_widgets()

    def on_touch_up(self, touch):
        """Return the held ingredient to the inventory when the cell is tapped."""
        if self.sprite_name is not None and self.collide_point(*touch.pos):
            name = self.sprite_name
            if self.remove_handler is not None:
                self.remove_handler(name)
            return True
        return super().on_touch_up(touch)


class PotionsScreen(KeyboardScreen):
    """Screen for brewing potions from flowers and preparing the run loadout."""

    def on_pre_enter(self):
        """Rebuild all brewing UI from the active profile state."""
        if not hasattr(self, "_recipe_page"):
            self._recipe_page = 0

        self.ids.title.text = _("Potion Crafting")
        self.ids.message_lbl.text = ""
        self.ids.spoon_lbl.text = _("Drag onto cauldron to mix")
        self.ids.back_btn.text = _("Back to Menu")
        self.ids.cauldron_img.source = get_asset_path("cauldron.png")
        self.ids.book_img.source = get_asset_path("recipes.png")
        self.ids.spoon.drag_image_source = get_asset_path("star.png")
        self.ids.spoon.drop_target = self.ids.cauldron_zone
        self.ids.spoon.drop_handler = lambda _touch: self._on_brew()

        self._render_recipe_book()
        self._refresh()

    def _refresh(self):
        """Re-render all dynamic areas of the brewing screen."""
        self._render_ingredient_strip()
        self._render_cauldron()
        self._render_potion_strip()
        self._render_run_slots()

    def _render_recipe_book(self):
        """Fill the recipe book panel with the current page's recipe details."""
        app = App.get_running_app()
        recipes = getattr(app, "recipes", [])
        if not recipes:
            name, desc, ingredients, duration = ("", "", "", "")
        else:
            recipe = recipes[self._recipe_page % len(recipes)]
            lines = [
                f"{_(sprite_name)} x{count}" for sprite_name, count in recipe.ingredients.items()
            ]
            name = _(recipe.name_key)
            desc = _(recipe.description_key)
            ingredients = "\n".join(lines)
            duration = _("Duration: ") + str(int(recipe.duration_seconds))
        self.ids.recipe_name_lbl.text = name
        self.ids.recipe_desc_lbl.text = desc
        self.ids.recipe_ingredients_lbl.text = ingredients
        self.ids.recipe_duration_lbl.text = duration

    def _flip_recipe(self, direction):
        """Move the recipe book by one page, wrapping around."""
        app = App.get_running_app()
        total = max(1, len(getattr(app, "recipes", [])))
        self._recipe_page = (self._recipe_page + direction) % total
        self._render_recipe_book()

    def _render_ingredient_strip(self):
        """Show one draggable chip per known flower type with count > 0."""
        app = App.get_running_app()
        strip = self.ids.ingredient_strip
        strip.clear_widgets()
        known_sprites = app.sprite_manager.names()
        inventory = app.profile_manager.get_inventory()
        for sprite_name in sorted(inventory):
            count = inventory[sprite_name]
            if count <= 0:
                continue
            if sprite_name not in known_sprites:
                logger.warning(
                    "Skipping unknown inventory sprite '%s' (legacy save data?)",
                    sprite_name,
                )
                continue
            chip = Draggable(size=(90, 110))
            chip.size_hint = (None, 1)
            sprite = app.sprite_manager.get(sprite_name)
            sprite.size = (56, 56)
            sprite.pos_hint = {"center_x": 0.5, "top": 1.0}
            label = Label(text=f"{_(sprite_name)} ({count}x)", font_size=15, color=(1, 1, 1, 1))
            label.wrap = True
            label.text_size = (86, 40)
            label.halign = "center"
            label.valign = "top"
            label.pos_hint = {"x": 0.02, "y": 0.0}
            chip.add_widget(sprite)
            chip.add_widget(label)
            chip.drop_target = self.ids.cauldron_zone
            chip.drop_handler = lambda _touch, s=sprite_name: self._on_ingredient_dropped(s)
            strip.add_widget(chip)

    def _render_cauldron(self):
        """Show current cauldron contents in the 2x2 slot grid."""
        app = App.get_running_app()
        grid = self.ids.cauldron_grid
        grid.clear_widgets()
        known_sprites = app.sprite_manager.names()
        contents = app.profile_manager.get_cauldron()
        for sprite_name, count in list(contents.items())[:4]:
            if sprite_name not in known_sprites:
                logger.warning(
                    "Skipping unknown cauldron sprite '%s' (legacy save data?)",
                    sprite_name,
                )
                continue
            slot = CauldronSlot(
                size=(95, 95),
                remove_handler=self._on_cauldron_ingredient_removed,
            )
            slot.size_hint = (None, None)
            slot.set_ingredient(sprite_name, count, app.sprite_manager.get(sprite_name))
            grid.add_widget(slot)

    def _render_potion_strip(self):
        """Show one draggable/clickable chip per potion with count > 0."""
        app = App.get_running_app()
        strip = self.ids.potion_strip
        strip.clear_widgets()
        shown = False
        for potion_id in sorted(app.profile_manager.get_potions()):
            count = app.profile_manager.get_potion_count(potion_id)
            if count <= 0:
                continue
            chip = Draggable(size=(160, 110))
            chip.size_hint = (None, 1)
            icon = Image(source=get_asset_path("star.png"))
            icon.size = (40, 40)
            icon.pos_hint = {"x": 0.05, "center_y": 0.5}
            label = Label(
                text=f"{_(potion_id + '_name')} ({count}x)", font_size=16, color=(1, 1, 1, 1)
            )
            label.wrap = True
            label.text_size = (105, 60)
            label.pos_hint = {"x": 0.28, "center_y": 0.5}
            chip.add_widget(icon)
            chip.add_widget(label)
            chip.drop_target = self.ids.run_slot_box
            chip.drop_handler = lambda touch, p=potion_id: self._on_potion_dropped(p, touch)
            chip.click_handler = lambda p=potion_id: self._on_potion_clicked(p)
            strip.add_widget(chip)
            shown = True
        if not shown:
            empty = Label(text="No potions yet", font_size=16, color=(0.7, 0.7, 0.7, 1))
            empty.pos_hint = {"x": 0.05, "center_y": 0.5}
            strip.add_widget(empty)

    def _render_run_slots(self):
        """Show the three next-run slots; empty ones labelled 1, 2, 3."""
        app = App.get_running_app()
        box = self.ids.run_slot_box
        box.clear_widgets()
        self._slot_buttons = []
        for index, potion_id in enumerate(app.profile_manager.get_run_loadout()):
            text = _(potion_id + "_name") if potion_id else str(index + 1)
            btn = Button(text=text, font_size=16)
            btn.bind(on_release=lambda _btn, i=index: self._on_run_slot_clicked(i))
            box.add_widget(btn)
            self._slot_buttons.append(btn)

    def _show_message(self, text, ok):
        """Show a status message, green on success and red on failure."""
        self.ids.message_lbl.text = text
        self.ids.message_lbl.color = (0.3, 1, 0.3, 1) if ok else (1, 0.3, 0.3, 1)

    def _on_ingredient_dropped(self, sprite_name):
        """Move one inventory flower unit into the cauldron."""
        app = App.get_running_app()
        try:
            app.profile_manager.move_flower_to_cauldron(sprite_name)
        except ProfileError as e:
            self._show_message(str(e), ok=False)
            return
        self._refresh()

    def _on_cauldron_ingredient_removed(self, sprite_name):
        """Move one cauldron ingredient unit back to the inventory."""
        app = App.get_running_app()
        try:
            app.profile_manager.move_cauldron_ingredient_to_inventory(sprite_name)
        except ProfileError as e:
            self._show_message(str(e), ok=False)
            return
        self._refresh()

    def _on_brew(self):
        """Mix the cauldron: brew the matching recipe or waste the ingredients."""
        app = App.get_running_app()
        contents = app.profile_manager.get_cauldron()
        if not contents:
            return
        recipe = match_recipe(contents, getattr(app, "recipes", []))
        app.profile_manager.clear_cauldron()
        if recipe is None:
            self._show_message(_("Ingredients wasted"), ok=False)
        else:
            app.profile_manager.add_potion(recipe.id)
            self._show_message(_("Brewed: ") + _(recipe.name_key), ok=True)
        self._refresh()

    def _on_potion_clicked(self, potion_id):
        """Place the potion into the first free run slot."""
        self._assign_potion(potion_id, None)

    def _on_potion_dropped(self, potion_id, touch):
        """Place the potion into the run slot under the touch, else the first free one."""
        for index, btn in enumerate(self._slot_buttons):
            if btn.collide_point(*touch.pos):
                self._assign_potion(potion_id, index)
                return
        self._assign_potion(potion_id, None)

    def _assign_potion(self, potion_id, slot_index):
        """Assign a potion to a run slot, showing an error message on failure."""
        app = App.get_running_app()
        try:
            app.profile_manager.assign_potion_to_slot(potion_id, slot_index)
        except ProfileError as e:
            self._show_message(str(e), ok=False)
            return
        self._refresh()

    def _on_run_slot_clicked(self, slot_index):
        """Return the potion from the clicked slot back to the potions inventory."""
        app = App.get_running_app()
        try:
            app.profile_manager.release_run_slot(slot_index)
        except ProfileError as e:
            self._show_message(str(e), ok=False)
            return
        self._refresh()

    def on_back(self):
        """Return to game menu hub when leaving the potions screen."""
        self.manager.current = "game_menu"


class GreenhouseScreen(KeyboardScreen):
    """Screen for greenhouse showcase (placeholder)."""

    def on_pre_enter(self):
        """Initialize greenhouse screen UI."""
        self.ids.title.text = _("Greenhouse")
        self.ids.desc.text = _("Placeholder Screen: Future greenhouse system will be here!")
        self.ids.back_btn.text = _("Back to Menu")

    def on_back(self):
        """Return to game menu hub when leaving the greenhouse screen."""
        self.manager.current = "game_menu"


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
        self.ids.menu_btn.text = _("Main Menu")

    def on_back(self):
        """Quit the app from the game over screen."""
        App.get_running_app().stop()

    def restart_game(self):
        """Restart game."""
        self.manager.current = "game"

    def goto_menu(self):
        """Go to the game menu hub."""
        self.manager.current = "game_menu"


class GameScreen(Screen):
    """Screen displaying the game view."""

    def on_enter(self):
        """Initialize game view and request keyboard on entry."""
        app = App.get_running_app()
        self.game_view = GameView(
            app.profile_manager,
            app.sprite_manager,
            app.levels,
            level_number=app.selected_level_number,
        )
        self.add_widget(self.game_view)
        self.game_view.start_game()

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def on_leave(self):
        """Stop game and release keyboard on leave."""
        if self._keyboard:
            self._keyboard.unbind(
                on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
            )
            self._keyboard = None
        self.game_view.stop_game()
        self.remove_widget(self.game_view)

    def _keyboard_closed(self):
        """Callback when keyboard is closed."""
        self._keyboard = None

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


Builder.load_string("""
<MenuScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 40
        spacing: 15
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: active_char_lbl
            font_size: 22
            color: 0.8, 0.8, 0.2, 1
        Label:
            id: subtitle
            font_size: 20
            color: 1, 1, 1, 1
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.15
            Button:
                id: start_btn
                font_size: 18
                on_release: root.start_game()
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.15
            Button:
                id: new_btn
                font_size: 18
                on_release: root.manager.current = 'new_character'
            Button:
                id: load_btn
                font_size: 18
                on_release: root.manager.current = 'load_character'
        Button:
            id: quit_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 18
            on_release: app.stop()

<GameMenuScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 40
        spacing: 15
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        BoxLayout:
            id: level_buttons
            orientation: 'vertical'
            spacing: 10
            size_hint_y: 0.5
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.15
            Button:
                id: potions_btn
                font_size: 18
                on_release: root.manager.current = 'potions'
            Button:
                id: greenhouse_btn
                font_size: 18
                on_release: root.manager.current = 'greenhouse'
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 18
            on_release: root.manager.current = 'menu'

<NewCharacterScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 32
            color: 1, 1, 1, 1
        TextInput:
            id: name_input
            multiline: False
            font_size: 24
            size_hint: (0.6, 0.25)
            pos_hint: {'center_x': 0.5}
        Label:
            id: error_label
            font_size: 20
            color: 1, 0, 0, 1
        Button:
            id: confirm_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.confirm()
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.back_to_menu()

<LoadCharacterScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 32
            color: 1, 1, 1, 1
            size_hint_y: 0.2
        ScrollView:
            size_hint_y: 0.6
            BoxLayout:
                id: list_layout
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 10
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.back_to_menu()

<GameWonScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 50
            color: 0.2, 0.8, 0.2, 1
        BoxLayout:
            id: harvest_box
            orientation: 'vertical'
            spacing: 10
            size_hint_y: 0.4
        Button:
            id: restart_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.restart_game()
        Button:
            id: menu_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.goto_menu()

<PotionsScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 12
        spacing: 6
        Label:
            id: title
            font_size: 32
            color: 1, 1, 1, 1
            size_hint_y: 0.1
        Label:
            id: message_lbl
            font_size: 18
            size_hint_y: 0.05
        ScrollView:
            do_scroll_x: True
            do_scroll_y: False
            size_hint_y: 0.19
            BoxLayout:
                id: ingredient_strip
                orientation: 'horizontal'
                spacing: 6
                size_hint_x: None
                width: self.minimum_width
                size_hint_y: 1
                padding: 4
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 1
            spacing: 10
            FloatLayout:
                id: cauldron_zone
                size_hint_x: 0.45
                padding: 8
                Image:
                    id: cauldron_img
                    size: (250, 250)
                    pos_hint: {'center': (0.5, 0.5)}
                GridLayout:
                    id: cauldron_grid
                    cols: 2
                    spacing: 4
                    size: (190, 190)
                    size_hint: (None, None)
                    pos_hint: {'center': (0.5, 0.5)}
                BoxLayout:
                    orientation: 'vertical'
                    size: (110, 120)
                    size_hint: (None, None)
                    pos_hint: {'x': 0, 'y': 0}
                    Draggable:
                        id: spoon
                        size_hint_y: 0.8
                        Image:
                            size: (70, 70)
                            pos_hint: {'center': (0.5, 0.5)}
                    Label:
                        id: spoon_lbl
                        font_size: 12
                        halign: 'center'
                        color: 0.8, 0.8, 0.8, 1
            BoxLayout:
                orientation: 'horizontal'
                size_hint_x: 0.55
                spacing: 6
                Button:
                    id: prev_recipe_btn
                    size_hint_x: 0.08
                    font_size: 20
                    text: '<<<'
                    on_release: root._flip_recipe(-1)
                FloatLayout:
                    id: book_page
                    Image:
                        id: book_img
                        allow_stretch: True
                        size_hint: (1, 1)
                        pos_hint: {'x': 0, 'y': 0}
                    BoxLayout:
                        orientation: 'vertical'
                        size_hint: (1, 1)
                        padding: 10
                        spacing: 4
                        canvas.before:
                            Color:
                                rgba: 0, 0, 0, 0.35
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        Label:
                            id: recipe_name_lbl
                            font_size: 22
                            color: 1, 1, 1, 1
                            wrap: True
                            text_size: self.size
                            halign: 'center'
                            valign: 'middle'
                            size_hint_y: 0.22
                        Label:
                            id: recipe_desc_lbl
                            font_size: 14
                            color: 0.9, 0.9, 0.9, 1
                            wrap: True
                            text_size: self.size
                            halign: 'center'
                            valign: 'middle'
                            size_hint_y: 0.4
                        Label:
                            id: recipe_ingredients_lbl
                            font_size: 15
                            color: 0.6, 1, 0.6, 1
                            wrap: True
                            text_size: self.size
                            halign: 'center'
                            valign: 'middle'
                            size_hint_y: 0.23
                        Label:
                            id: recipe_duration_lbl
                            font_size: 13
                            color: 0.8, 0.8, 0.8, 1
                            wrap: True
                            text_size: self.size
                            halign: 'center'
                            valign: 'middle'
                            size_hint_y: 0.15
                Button:
                    id: next_recipe_btn
                    size_hint_x: 0.08
                    font_size: 20
                    text: '>>>'
                    on_release: root._flip_recipe(1)
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.2
            spacing: 8
            BoxLayout:
                id: run_slot_box
                orientation: 'horizontal'
                size_hint_x: 0.4
                spacing: 6
            ScrollView:
                do_scroll_x: True
                do_scroll_y: False
                size_hint_x: 0.6
                BoxLayout:
                    id: potion_strip
                    orientation: 'horizontal'
                    spacing: 6
                    size_hint_x: None
                    width: self.minimum_width
                    size_hint_y: 1
                    padding: 4
        Button:
            id: back_btn
            size_hint: (0.3, 0.08)
            pos_hint: {'center_x': 0.5}
            font_size: 16
            on_release: root.on_back()

<GreenhouseScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: desc
            font_size: 24
            color: 0.7, 0.7, 0.7, 1
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.on_back()

<QuitScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: cont_lbl
            font_size: 24
            color: 1, 1, 1, 1
        Label:
            id: quit_lbl
            font_size: 24
            color: 1, 1, 1, 1
        Button:
            id: resume_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.resume_game()
        Button:
            id: quit_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: app.stop()

<GameOverScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 50
            color: 1, 1, 1, 1
        Label:
            id: score_lbl
            font_size: 28
            color: 1, 1, 1, 1
        Label:
            id: distance_lbl
            font_size: 28
            color: 1, 1, 1, 1
        Button:
            id: restart_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.restart_game()
        Button:
            id: menu_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.goto_menu()
""")
