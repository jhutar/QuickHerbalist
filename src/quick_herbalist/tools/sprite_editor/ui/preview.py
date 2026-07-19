from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock

class SpritePreviewWidget(BoxLayout):
    """
    A widget that displays an animated preview of a sprite and allows zooming.
    """
    zoom_level = NumericProperty(1.0)
    sprite_name = ObjectProperty(None)
    frames = ListProperty([])  # List of dicts: {'image': str, 'duration': int}

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self._setup_ui()
        Clock.schedule_interval(self._animate, 1/24.0)

    def _setup_ui(self):
        # Zoom controls
        zoom_controls = BoxLayout(size_hint_y=None, height='40dp', orientation='horizontal')
        zoom_controls.add_widget(Button(text='- Zoom', on_release=self.zoom_out))
        zoom_controls.add_widget(Button(text='100%', on_release=self.reset_zoom))
        zoom_controls.add_widget(Button(text='+ Zoom', on_release=self.zoom_in))
        self.add_widget(zoom_controls)

        # Zoom level label
        self.zoom_label = Label(text="Zoom: 100%", size_hint_y=None, height='20dp')
        self.add_widget(self.zoom_label)

        # ScrollView for zooming
        self.scroll_view = ScrollView()
        self.image = Image()
        self.image.size_hint = (None, None)
        self.scroll_view.add_widget(self.image)
        self.add_widget(self.scroll_view)

    def zoom_in(self, instance):
        levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        try:
            idx = levels.index(self.zoom_level)
            if idx < len(levels) - 1:
                self.zoom_level = levels[idx + 1]
            else:
                self.zoom_level = levels[-1]
        except ValueError:
            self.zoom_level = 1.0
        self._update_zoom_ui()

    def zoom_out(self, instance):
        levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        try:
            idx = levels.index(self.zoom_level)
            if idx > 0:
                self.zoom_level = levels[idx - 1]
            else:
                self.zoom_level = levels[0]
        except ValueError:
            self.zoom_level = 1.0
        self._update_zoom_ui()

    def reset_zoom(self, instance):
        self.zoom_level = 1.0
        self._update_zoom_ui()

    def _update_zoom_ui(self):
        self.zoom_label.text = f"Zoom: {int(self.zoom_level * 100)}%"
        if self.image.texture:
            base_w = self.image.texture.size[0]
            base_h = self.image.texture.size[1]
        else:
            base_w = 256
            base_h = 256
        self.image.size = (base_w * self.zoom_level, base_h * self.zoom_level)

    def _animate(self, dt):
        # Placeholder for animation logic
        pass

    def set_texture(self, texture):
        self.image.texture = texture
        self._update_zoom_ui()
