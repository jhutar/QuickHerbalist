"""Potion brewing screen: ingredient/recipe/cauldron/potion/loadout panels."""

import logging

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from quick_herbalist.core.config_parser import get_asset_path
from quick_herbalist.localization import _
from quick_herbalist.potions import match_recipe
from quick_herbalist.profiles import ProfileError
from quick_herbalist.screens.base import KeyboardScreen, load_screen_kv
from quick_herbalist.screens.widgets import Draggable

logger = logging.getLogger(__name__)


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
        self.ids.back_btn.text = _("Back to Game Menu")
        self.ids.cauldron_img.source = get_asset_path("cauldron.png")
        self.ids.book_img.source = get_asset_path("recipes.png")
        self.ids.spoon_img.source = get_asset_path("spoon.png")
        self.ids.spoon.drag_image_source = get_asset_path("spoon.png")
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
            chip.click_handler = lambda s=sprite_name: self._on_ingredient_dropped(s)
            chip.drag_image_source = get_asset_path(sprite.frames_data[0]["image"])
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
            self._show_message(_("Cauldron is empty"), ok=False)
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


load_screen_kv("potions.kv")
