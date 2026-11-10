"""Phase 0 spike: minimal Kivy webgl app for Emscripten (WASM) verification.

Checks: .kv loading, Clock game loop, Window.request_keyboard focus,
preload-file sprite. All verification events print "SPIKE: ..." lines so a
headless browser can capture them via the console.
"""

import os
import struct
import zlib


def _ensure_block_png():
    """Write block.png if missing (standalone bundle preloads it instead)."""
    if os.path.exists("block.png"):
        return
    w = h = 64
    row = b"\x00" + b"\x48\x30\x18\xff" * w

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * h))
        + chunk(b"IEND", b"")
    )
    with open("block.png", "wb") as f:
        f.write(png)


_ensure_block_png()

from kivy.config import Config  # noqa: E402

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "600")
Config.set("graphics", "resizable", "0")

from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.core.image import Image  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.lang import Builder  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402


def _tick_clock(_dt):
    """Log throttled Clock ticks to prove the game loop runs under webgl."""
    if _tick_clock.count % 30 == 1:
        print(f"SPIKE: tick {_tick_clock.count}", flush=True)
    _tick_clock.count += 1


_tick_clock.count = 0


class SpriteBox(Widget):
    """Root widget holding the sprite (see .kv)."""


class SpikeApp(App):
    """Minimal app: one preloaded sprite, .kv layout, keyboard."""

    def build(self):
        """Build root from the .kv next to this module, attach keyboard."""
        kv_path = os.path.join(
            os.path.dirname(__file__), os.path.splitext(os.path.basename(__file__))[0] + ".kv"
        )
        root = Builder.load_file(kv_path)
        sprite = root.ids.sprite  # kivy 3 dropped Widget.find_class; use kv ids
        sprite.source = "block.png"
        img = Image(sprite.source)  # kivy 3: lazy provider; .size triggers load
        assert tuple(img.size) == (64, 64), "sprite missing"
        print("SPIKE: kv loaded + sprite decoded", flush=True)

        keyboard = Window.request_keyboard(self._keyboard_closed, root)
        keyboard.bind(on_key_down=self._on_key_down)  # kivy 3: no .show()
        print("SPIKE: keyboard attached", flush=True)

        Clock.schedule_interval(_tick_clock, 1 / 60)
        print("SPIKE: app started", flush=True)
        return root

    def _keyboard_closed(self):
        """Handle keyboard focus loss."""
        print("SPIKE: keyboard closed", flush=True)

    def _on_key_down(self, keyboard, keycode, string, modifiers):
        """Handle key press; report the key name for verification."""
        print(f"SPIKE: key down {keycode[1]}", flush=True)


if __name__ == "__main__":
    SpikeApp().run()
