"""HUD labels for the game scene: score, distance, active effects, character."""

from kivy.uix.label import Label
from kivy.uix.widget import Widget

from quick_herbalist.localization import _


class GameHud(Widget):
    """Fixed-position HUD labels for one game run."""

    def __init__(self, **kwargs):
        """Create the score, distance, effect, and character labels."""
        super().__init__(**kwargs)
        self.score_label = self._make_label(font_size=24, pos=(10, 560))
        self.distance_label = self._make_label(font_size=24, pos=(10, 520))
        self.effect_label = self._make_label(
            font_size=20, pos=(10, 420), size=(250, 90), valign="top"
        )
        self.char_label = self._make_label(
            font_size=24, pos=(590, 560), halign="right"
        )

    @staticmethod
    def _make_label(font_size, pos, size=(200, 30), halign="left", valign="middle"):
        """Create one black HUD label at a fixed position with sized text."""
        label = Label(
            text="",
            font_size=font_size,
            color=(0, 0, 0, 1),
            pos=pos,
            size=size,
            halign=halign,
            valign=valign,
        )
        label.bind(size=label.setter("text_size"))
        return label

    def set_score(self, score):
        """Show the collected counter."""
        self.score_label.text = _("Collected: ") + str(score)

    def set_distance(self, distance):
        """Show the traveled distance in whole units."""
        self.distance_label.text = _("Distance: ") + str(int(distance))

    def set_character(self, active_name, level_number):
        """Show the active character name and the current level number."""
        name = active_name if active_name else _("No Active Character")
        self.char_label.text = f"{name}  {_('Level: ')}{level_number}"

    def set_effects(self, lines):
        """Show active effect names with remaining seconds, one per line."""
        self.effect_label.text = "\n".join(lines)
