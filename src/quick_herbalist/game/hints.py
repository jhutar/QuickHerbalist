"""First-seen entity tutorial hints: per-type content and the pause popup box.

The scene (game.scene.GameView) decides *when* a hint is due and owns the
pause/queue; this module only carries the hint text per entity type and the
HintBox widget that renders one hint.
"""

from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from quick_herbalist.game.widgets import SCREEN_H, SCREEN_W
from quick_herbalist.localization import _

# Entity type -> (title, description), translated at import time so the
# literals stay extractable by scripts/update_pot.py.
ENTITY_HINTS = {
    "flower": (
        _("Flower"),
        _("Flowers are collectible. Run through them to add them to your harvest."),
    ),
    "stone": (
        _("Stone"),
        _("Stones are obstacles you need to avoid. If you run into them, your mission is over."),
    ),
    "rock": (
        _("Rock"),
        _("Rocks are huge obstacles you cannot pass. If you run into them, your mission is over."),
    ),
    "spider": (
        _("Spider"),
        _("Spiders crawl toward you and their sting ends the run. Keep your distance."),
    ),
    "hill": (
        _("Hill"),
        _("Hills are safe, but they slow you down while you run through them."),
    ),
}

# Fixed box geometry (screen is fixed size, see widgets.SCREEN_W/SCREEN_H).
BOX_W = 500
BOX_H = 220
BOX_X = (SCREEN_W - BOX_W) / 2
BOX_Y = (SCREEN_H - BOX_H) / 2
IMAGE_SIZE = 96
CLOSE_BTN_SIZE = 48

_TITLE_FONT = 28
_DESC_FONT = 18
_WHITE = (1, 1, 1, 1)
# Opaque fill so hint text never sits on top of the game scene.
_BG = (0.1, 0.1, 0.1, 1.0)


def hint_text(entity_type):
    """Return the (title, description) pair for an entity type."""
    return ENTITY_HINTS[entity_type]


class HintBox(Widget):
    """Centered tutorial popup for one entity, shown while the run is paused.

    Layout: solid dark background filling the box, entity image left,
    title upper-right, description lower-right, cross button in the
    upper-right corner. Closes via the cross button or keyboard
    (Esc/Enter/Space, handled by the scene); any other touch is swallowed
    while open so no game input gets through.
    """

    def __init__(self, sprite_manager, sprite_name, title, description, on_close, **kwargs):
        """Build the box for one entity; on_close fires once when it is dismissed."""
        super().__init__(**kwargs)
        self.size = (SCREEN_W, SCREEN_H)  # full screen: catches all input
        self.pos = (0, 0)
        self._on_close = on_close
        self.box_rect = (BOX_X, BOX_Y, BOX_W, BOX_H)
        self.close_rect = (
            BOX_X + BOX_W - CLOSE_BTN_SIZE - 10,
            BOX_Y + BOX_H - CLOSE_BTN_SIZE - 10,
            CLOSE_BTN_SIZE,
            CLOSE_BTN_SIZE,
        )
        # Solid background behind the box for text readability.
        self.bg_rect = (BOX_X, BOX_Y, BOX_W, BOX_H)
        with self.canvas:
            Color(*_BG)
            Rectangle(pos=self.bg_rect[:2], size=self.bg_rect[2:4])

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
        """Close on touch of the cross; swallow all other touches."""
        if self._touch_in(touch.pos, self.close_rect):
            self._on_close()
        return True  # cross closes; everything else is consumed without dismissal

    @staticmethod
    def _touch_in(pos, rect):
        """Return True if the (x, y) point is inside the (x, y, w, h) rectangle."""
        x, y, w, h = rect
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h
