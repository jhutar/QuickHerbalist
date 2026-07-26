import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from quick_herbalist.core.config_parser import get_asset_path


class SpritePreviewWidget(BoxLayout):
    """
    A widget that displays an animated preview of a sprite and allows zooming.
    """

    zoom_level = NumericProperty(1.0)
    sprite_name = ObjectProperty(None)
    frames = ListProperty(
        []
    )  # List of dicts: {'atlas_id': str, 'duration': int, 'image': str, 'x': int, 'y': int, 'w': int, 'h': int}

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.current_frame_index = 0
        self.anim_time = 0.0
        self._setup_ui()
        Clock.schedule_interval(self._animate, 1 / 30.0)

    def _setup_ui(self):
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
        levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        try:
            idx = levels.index(self.zoom_level)
            if idx < len(levels) - 1:
                self.zoom_level = levels[idx + 1]
        except ValueError:
            self.zoom_level = 1.0
        self._update_zoom_ui()

    def zoom_out(self, instance=None):
        levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        try:
            idx = levels.index(self.zoom_level)
            if idx > 0:
                self.zoom_level = levels[idx - 1]
        except ValueError:
            self.zoom_level = 1.0
        self._update_zoom_ui()

    def reset_zoom(self, instance=None):
        self.zoom_level = 1.0
        self._update_zoom_ui()

    def _update_zoom_ui(self):
        self.zoom_label.text = f"Zoom: {int(self.zoom_level * 100)}%"
        if self.frames and self.current_frame_index < len(self.frames):
            frame_info = self.frames[self.current_frame_index]
            w = int(frame_info.get("w", 32))
            h = int(frame_info.get("h", 32))
            self.image.size = (w * self.zoom_level, h * self.zoom_level)
        else:
            self.image.size = (256 * self.zoom_level, 256 * self.zoom_level)

    def _animate(self, dt):
        if not self.frames:
            self.image.texture = None
            return

        self.anim_time += dt * 1000
        frame_info = self.frames[self.current_frame_index % len(self.frames)]
        duration = frame_info.get("duration", 250)

        # If we edited frames, index might be out of range
        if self.current_frame_index >= len(self.frames):
            self.current_frame_index = 0
            self.anim_time = 0.0

        if self.anim_time >= duration:
            self.anim_time = 0.0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self._load_current_frame_texture()

    def _load_current_frame_texture(self):
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
        self.current_frame_index = 0
        self.anim_time = 0.0
        self._load_current_frame_texture()

    def force_refresh(self):
        self.anim_time = 0.0
        self._load_current_frame_texture()
        self._update_zoom_ui()
