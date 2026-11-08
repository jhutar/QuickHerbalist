"""First-seen entity tutorial hints: per-type content and the pause popup box.

The scene (game.scene.GameView) decides *when* a hint is due and owns the
pause/queue; this module only carries the hint text per entity type and the
HintBox widget that renders one hint.
"""

from kivy.uix.label import Label
from kivy.uix.widget import Widget

from quick_herbalist.game.widgets import SCREEN_H, SCREEN_W
from quick_herbalist.localization import _

# Entity type -> (title, description); both strings are localization msgids.
ENTITY_HINTS = {
    "flower": (
        "Flower",
        "Flowers are collectible. Run through them to add them to your harvest.",
    ),
    "stone": (
        "Stone",
        "Stones are obstacles you need to avoid. If you run into them, your mission is over.",
    ),
    "rock": (
        "Rock",
        "Rocks are huge obstacles you cannot pass. If you run into them, your mission is over.",
    ),
    "spider": (
        "Spider",
        "Spiders crawl toward you and their sting ends the run. Keep your distance.",
    ),
    "hill": (
        "Hill",
        "Hills are safe, but they slow you down while you run through them.",
    ),
}

# Fixed box geometry (screen is fixed size, see widgets.SCREEN_W/SCREEN_H).
BOX_W = 500
BOX_H = 220
BOX_X = (SCREEN_W - BOX_W) / 2
BOX_Y = (SCREEN_H - BOX_H) / 2
IMAGE_SIZE = 96
CLOSE_BTN_SIZE = 36

_TITLE_FONT = 28
_DESC_FONT = 18
_WHITE = (1, 1, 1, 1)


def hint_text(entity_type):
    """Return the translated (title, description) pair for an entity type."""
    title, description = ENTITY_HINTS[entity_type]
    return _(title), _(description)


class HintBox(Widget):
    """Centered tutorial popup for one entity, shown while the run is paused.

    Layout: entity image left, title upper-right, description lower-right,
    cross button in the upper-right corner. Closes via the cross or a touch
    outside the box; keyboard dismissal (Esc/Enter/Space) is handled by the
    scene. Swallows every touch while open so no game input gets through.
    """

    def __init__(self, sprite_manager, sprite_name, title, description, on_close, **kwargs):
        """Build the box for one entity; on_close fires once when it is dismissed."""
        super().__init__(**kwargs)
        self.size = (SCREEN_W, SCREEN_H)  # full screen: catches all input
        self.pos = (0, 0)
        self._on_close = on_close
        self.box_rect = (BOX_X, BOX_Y, BOX_W, BOX_H)
        self.close_rect = (BOX_X + BOX_W - CLOSE_BTN_SIZE - 10, BOX_Y + BOX_H - CLOSE_BTN_SIZE - 10,
                           CLOSE_BTN_SIZE, CLOSE_BTN_SIZE)

        image = sprite_manager.get(sprite_name)
        image.pos = (BOX_X + 20, BOX_Y + (BOX_H - IMAGE_SIZE) / 2)
        image.size = (IMAGE_SIZE, IMAGE_SIZE)
        self.add_widget(image)

        self.add_widget(
            Label(
                text=title,
                font_size=_TITLE_FONT,
                color=_WHITE,
                halign="right",
                size=(BOX_W - IMAGE_SIZE - 60, 60),
                pos=(BOX_X + IMAGE_SIZE + 40, BOX_Y + BOX_H - 70),
            )
        )
        self.add_widget(
            Label(
                text=description,
                font_size=_DESC_FONT,
                color=_WHITE,
                halign="right",
                valign="bottom",
                wrap=True,
                size=(BOX_W - IMAGE_SIZE - 40, 110),
                pos=(BOX_X + IMAGE_SIZE + 40, BOX_Y + 10),
            )
        )
        self.add_widget(
            Label(
                text="✕",
                font_size=_TITLE_FONT,
                color=_WHITE,
                size=self.close_rect[2:4],
                pos=self.close_rect[0:2],
            )
        )

    def on_touch_down(self, touch):
        """Close on touch of the cross or outside the box; swallow all touches."""
        if not self._touch_in(touch.pos, self.box_rect):
            self._on_close()
            return True
        if self._touch_in(touch.pos, self.close_rect):
            self._on_close()
            return True
        return True  # touch inside the box: consume, no dismissal

    @staticmethod
    def _touch_in(pos, rect):
        """Return True if the (x, y) point is inside the (x, y, w, h) rectangle."""
        x, y, w, h = rect
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h
