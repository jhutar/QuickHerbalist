import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from quick_herbalist.core.animated_sprite import AnimationStateController
from quick_herbalist.core.config_parser import get_asset_path


class SpritePreviewWidget(BoxLayout):
    """
    A widget that displays an animated preview of a sprite and allows zooming.
    """

    zoom_level = NumericProperty(1.0)
    sprite_name = ObjectProperty(None)
    frames = ListProperty(
        []
    )  # List of dicts: {'atlas_id': str, 'duration_ms': int, 'image': str, 'x': int, 'y': int, 'w': int, 'h': int}

    def __init__(self, **kwargs):
        """Initialize the widget with zoom controls, scroll view, and animation loop."""
        super().__init__(orientation="vertical", **kwargs)
        # Delegate clock-ticks and frame transitions to the shared controller
        self.controller = AnimationStateController([])
        self._setup_ui()
        Clock.schedule_interval(self._animate, 1 / 30.0)

    def _setup_ui(self):
        """Build the widget UI: zoom controls, label, scroll view, and debug info."""
        # Zoom controls
        zoom_controls = BoxLayout(
            size_hint_y=None, height="40dp", orientation="horizontal"
        )
        zoom_controls.add_widget(Button(text="- Zoom", on_release=self.zoom_out))
        zoom_controls.add_widget(Button(text="100%", on_release=self.reset_zoom))
        zoom_controls.add_widget(Button(text="+ Zoom", on_release=self.zoom_in))
        self.add_widget(zoom_controls)

        # Zoom level label
        self.zoom_label = Label(text="Zoom: 100%", size_hint_y=None, height="20dp")
        self.add_widget(self.zoom_label)

        # ScrollView for zooming
        self.scroll_view = ScrollView()
        self.image = Image()
        self.image.size_hint = (None, None)
        self.scroll_view.add_widget(self.image)
        self.add_widget(self.scroll_view)

        # Debug label for currently animated Atlas ID
        self.debug_label = Label(
            text="Current Atlas ID: None", size_hint_y=None, height="30dp", bold=True
        )
        self.add_widget(self.debug_label)

    def zoom_in(self, instance=None):
        """Increment zoom level to the next preset value."""
        levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        try:
            idx = levels.index(self.zoom_level)
            if idx < len(levels) - 1:
                self.zoom_level = levels[idx + 1]
        except ValueError:
            self.zoom_level = 1.0
        self._update_zoom_ui()

    def zoom_out(self, instance=None):
        """Decrement zoom level to the previous preset value."""
        levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        try:
            idx = levels.index(self.zoom_level)
            if idx > 0:
                self.zoom_level = levels[idx - 1]
        except ValueError:
            self.zoom_level = 1.0
        self._update_zoom_ui()

    def reset_zoom(self, instance=None):
        """Reset zoom to 100% (1.0 factor)."""
        self.zoom_level = 1.0
        self._update_zoom_ui()

    def _update_zoom_ui(self):
        """Update the zoom label text and image size to match current zoom level."""
        self.zoom_label.text = f"Zoom: {int(self.zoom_level * 100)}%"
        if self.frames and self.current_frame_index < len(self.frames):
            frame_info = self.frames[self.current_frame_index]
            w = int(frame_info.get("w", 32))
            h = int(frame_info.get("h", 32))
            self.image.size = (w * self.zoom_level, h * self.zoom_level)
        else:
            self.image.size = (256 * self.zoom_level, 256 * self.zoom_level)

    @property
    def current_frame_index(self):
        """Index of the frame currently shown, delegated to the controller."""
        return self.controller.current_frame_index

    def _animate(self, dt):
        """Clock callback that ticks the controller and reloads frame on change."""
        if not self.frames:
            self.image.texture = None
            return

        if self.controller.tick(dt):
            self._load_current_frame_texture()

    def _load_current_frame_texture(self):
        """Load the texture for the current frame index into the image widget."""
        if not self.frames:
            self.image.texture = None
            self.debug_label.text = "Current Atlas ID: None"
            return

        frame_info = self.frames[self.current_frame_index % len(self.frames)]
        atlas_id = frame_info.get("atlas_id", "")
        self.debug_label.text = f"Current Atlas ID: {atlas_id}"
        image_filename = frame_info.get("image", "")
        x = int(frame_info.get("x", 0))
        y = int(frame_info.get("y", 0))
        w = int(frame_info.get("w", 32))
        h = int(frame_info.get("h", 32))

        if not image_filename:
            self.image.texture = None
            return

        full_path = get_asset_path(image_filename)
        if not os.path.exists(full_path):
            self.image.texture = None
            return

        try:
            core_img = CoreImage(full_path)
            tex_w, tex_h = core_img.texture.size
            # Sanitize coordinates
            x = max(0, min(x, tex_w - 1))
            y = max(0, min(y, tex_h - 1))
            w = max(1, min(w, tex_w - x))
            h = max(1, min(h, tex_h - y))

            self.image.texture = core_img.texture.get_region(x, y, w, h)
            self.image.size = (w * self.zoom_level, h * self.zoom_level)
        except Exception:
            self.image.texture = None

    def on_frames(self, instance, value):
        """Callback when frames property changes; reset animation and reload frame."""
        self.controller.set_frames(value)
        self._load_current_frame_texture()

    def force_refresh(self):
        """Reset animation timer and reload current frame texture."""
        self.controller.reset_time()
        self._load_current_frame_texture()
        self._update_zoom_ui()
