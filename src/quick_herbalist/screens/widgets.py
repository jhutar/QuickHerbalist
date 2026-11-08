"""Reusable screen widgets (drag & drop) not tied to a single screen."""

from kivy.factory import Factory
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image


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
