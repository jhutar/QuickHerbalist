from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from .preview import SpritePreviewWidget
from .sequence_editor import SequenceEditorWidget
from quick_herbalist.core.config_parser import ConfigStitcher, get_asset_path


class SpriteEditorMainLayout(BoxLayout):
    """
    The main layout of the Sprite Editor.
    Delegates all domain-level config parsing, file reads/writes,
    and schema coordinate mapping to the ConfigStitcher.
    """

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", spacing=10, padding=10, **kwargs)
        self.yaml_path = get_asset_path("sprites.yaml")
        self.atlas_path = get_asset_path("sprites.atlas")

        # Initialize the domain ConfigStitcher controller
        self.stitcher = ConfigStitcher(self.yaml_path, self.atlas_path)
        self.selected_sprite = ""

        self._setup_ui()
        self._populate_sprite_list()

    def _setup_ui(self):
        # 1. Left Sidebar (Sprite List and creation)
        sidebar = BoxLayout(
            orientation="vertical", size_hint_x=None, width="200dp", spacing=10
        )
        sidebar.add_widget(
            Label(text="Sprites List", size_hint_y=None, height="40dp", bold=True)
        )

        # Scrollable sprite list container
        self.sprite_list_scroll = ScrollView()
        self.sprite_list_container = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=5
        )
        self.sprite_list_container.bind(
            minimum_height=self.sprite_list_container.setter("height")
        )
        self.sprite_list_scroll.add_widget(self.sprite_list_container)
        sidebar.add_widget(self.sprite_list_scroll)

        # Create/Delete controls
        sidebar.add_widget(
            Label(text="New Sprite Name:", size_hint_y=None, height="20dp")
        )
        self.new_sprite_input = TextInput(
            multiline=False, size_hint_y=None, height="35dp"
        )
        sidebar.add_widget(self.new_sprite_input)

        sidebar_btns = BoxLayout(
            orientation="horizontal", size_hint_y=None, height="40dp", spacing=5
        )
        new_btn = Button(text="Create", on_release=self.create_sprite)
        delete_btn = Button(
            text="Delete",
            on_release=self.delete_sprite,
            background_color=[0.8, 0.2, 0.2, 1],
        )
        sidebar_btns.add_widget(new_btn)
        sidebar_btns.add_widget(delete_btn)
        sidebar.add_widget(sidebar_btns)

        self.add_widget(sidebar)

        # 2. Middle Editor Section
        self.editor = SequenceEditorWidget(
            save_callback=self.on_save_callback,
            frames_changed_callback=self.on_frames_changed,
            size_hint_x=0.5,
        )
        self.add_widget(self.editor)

        # 3. Right Preview Section
        self.preview = SpritePreviewWidget(size_hint_x=0.3)
        self.add_widget(self.preview)

    def _populate_sprite_list(self):
        self.sprite_list_container.clear_widgets()
        for name in self.stitcher.get_sprite_list():
            btn = Button(text=name, size_hint_y=None, height="35dp")
            btn.bind(on_release=lambda instance, n=name: self.select_sprite(n))
            if name == self.selected_sprite:
                btn.background_color = [0.2, 0.6, 1, 1]  # Highlight selected
            self.sprite_list_container.add_widget(btn)

    def select_sprite(self, name):
        self.selected_sprite = name
        self._populate_sprite_list()

        # Build fully loaded frames for this sprite via the stitcher
        frames = self.stitcher.get_sprite_frames(name)

        self.editor.set_sprite_name(name)
        self.editor.load_frames(frames)
        self.preview.sprite_name = name
        self.preview.frames = frames

    def on_frames_changed(self, updated_frames):
        # Dynamically push updated frames to the preview
        self.preview.frames = list(updated_frames)
        self.preview.force_refresh()

    def create_sprite(self, instance):
        name = self.new_sprite_input.text.strip()
        if not name:
            return
        if not self.stitcher.create_sprite(name):
            print(f"Sprite '{name}' already exists or is invalid.")
            return

        self.new_sprite_input.text = ""
        self.select_sprite(name)

    def delete_sprite(self, instance):
        if not self.selected_sprite:
            return

        self.stitcher.delete_sprite(self.selected_sprite)

        self.selected_sprite = ""
        self.editor.set_sprite_name("")
        self.editor.load_frames([])
        self.preview.sprite_name = ""
        self.preview.frames = []
        self._populate_sprite_list()

    def on_save_callback(self, sprite_name, frames):
        if not sprite_name:
            print("No sprite name specified. Cannot save.")
            return

        try:
            self.stitcher.save_sprite_frames(sprite_name, frames)
            print(f"Successfully saved sprite '{sprite_name}' via ConfigStitcher")
            self.select_sprite(sprite_name)
        except Exception as e:
            print(f"Error saving sprite {sprite_name}: {e}")
