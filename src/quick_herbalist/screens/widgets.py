"""Reusable screen widgets (drag & drop) not tied to a single screen."""

from kivy.core.window import Window
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget


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


class OptionMenu(Widget):
    """Dropdown selector that dispatches `on_select` when an option is picked.

    Clicking the header opens a vertical list of option buttons above it.
    A full-window catcher swallows outside touches and closes the list.
    """

    def __init__(self, **kwargs):
        """Build the header button and store the dropdown options."""
        self.options = kwargs.pop("options", [])
        self._value = ""
        self._dropdown = []
        self.font_size = kwargs.pop("font_size", 14)
        self._header = Button(size_hint=(1, 1), font_size=self.font_size)
        self._header.bind(on_release=self._on_header_release)
        super().__init__(**kwargs)
        self.add_widget(self._header)
        self.bind(size=self._sync_header, pos=self._sync_header)
        self._sync_header()
        self.value = ""

    @property
    def value(self):
        """Currently selected option label."""
        return self._value

    @value.setter
    def value(self, new_value):
        """Update the selected option and the header text."""
        self._value = new_value
        self._header.text = str(new_value)

    def _sync_header(self, *args):
        """Keep the header button covering the whole OptionMenu area."""
        self._header.size = self.size
        self._header.pos = self.pos

    def _on_header_release(self, instance, touch):
        """Open the dropdown when the release lands on the header."""
        if instance.collide_point(*touch.pos):
            self._open_dropdown()

    def _open_dropdown(self):
        """Show a touch catcher plus one button per option above the header."""
        self._close_dropdown()
        box = BoxLayout(orientation="vertical", spacing=0, padding=2)
        box.size = (self.size[0], 50 * len(self.options))
        for option in self.options:
            box.add_widget(self._make_option_button(option))
        box.pos = (self.pos[0], self.pos[1] + self.size[1])
        catcher = Widget(size=Window.size, pos=(0, 0))
        catcher.bind(on_touch_down=self._on_catcher_touch)
        Window.add_widget(catcher)
        Window.add_widget(box)
        self._dropdown = [catcher, box]

    def _make_option_button(self, option):
        """Build one clickable option button bound to _select_option."""
        button = Button(text=str(option), size_hint_y=None, height=50, font_size=self.font_size)
        button.bind(on_release=lambda _btn, touch=None, opt=option: self._select_option(opt))
        return button

    def _on_catcher_touch(self, touch):
        """Close the dropdown and consume the outside touch."""
        self._close_dropdown()
        return True

    def _close_dropdown(self):
        """Remove catcher and option list from the root window."""
        for widget in self._dropdown:
            Window.remove_widget(widget)
        self._dropdown = []

    def _select_option(self, option):
        """Commit the choice, close the dropdown and fire on_select."""
        self._close_dropdown()
        self.value = option
        self.dispatch("on_select")


# KV rules resolve widget names through the Factory only
Factory.register("Draggable", cls=Draggable)
Factory.register("OptionMenu", cls=OptionMenu)
