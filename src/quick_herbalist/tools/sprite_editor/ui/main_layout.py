import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from .preview import SpritePreviewWidget
from .sequence_editor import SequenceEditorWidget
from quick_herbalist.core.config_parser import (
    load_sprites_yaml,
    load_sprites_atlas,
    save_sprites_yaml,
    save_sprites_atlas,
    get_asset_path,
)


class SpriteEditorMainLayout(BoxLayout):
    """
    The main layout of the Sprite Editor.
    Brings together:
    1. Left Sidebar: Sprite list, creation, deletion.
    2. Middle Section: Frame Sequence and Duration Editor.
    3. Right Section: Animated Preview with Zoom.
    """

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", spacing=10, padding=10, **kwargs)
        self.yaml_path = get_asset_path("sprites.yaml")
        self.atlas_path = get_asset_path("sprites.atlas")

        # Load configurations safely on startup
        self.sprites_yaml_data = {}
        self.sprites_atlas_data = {}
        self._load_configs()

        self.selected_sprite = ""

        self._setup_ui()
        self._populate_sprite_list()

    def _load_configs(self):
        try:
            if os.path.exists(self.yaml_path):
                self.sprites_yaml_data = load_sprites_yaml(self.yaml_path)
            if not self.sprites_yaml_data or "sprites" not in self.sprites_yaml_data:
                self.sprites_yaml_data = {"sprites": {}}

            if os.path.exists(self.atlas_path):
                self.sprites_atlas_data = load_sprites_atlas(self.atlas_path)
            if not self.sprites_atlas_data:
                self.sprites_atlas_data = {}
        except Exception as e:
            print(f"Error loading configurations: {e}")
            self.sprites_yaml_data = {"sprites": {}}
            self.sprites_atlas_data = {}

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
            on_save_callback=self.on_save_callback,
            on_frames_changed_callback=self.on_frames_changed,
            size_hint_x=0.5,
        )
        self.add_widget(self.editor)

        # 3. Right Preview Section
        self.preview = SpritePreviewWidget(size_hint_x=0.3)
        self.add_widget(self.preview)

    def _populate_sprite_list(self):
        self.sprite_list_container.clear_widgets()
        sprites = self.sprites_yaml_data.get("sprites", {})
        for name in sorted(sprites.keys()):
            btn = Button(text=name, size_hint_y=None, height="35dp")
            btn.bind(on_release=lambda instance, n=name: self.select_sprite(n))
            if name == self.selected_sprite:
                btn.background_color = [0.2, 0.6, 1, 1]  # Highlight selected
            self.sprite_list_container.add_widget(btn)

    def select_sprite(self, name):
        self.selected_sprite = name
        self._populate_sprite_list()

        # Build fully loaded frames for this sprite
        frames = []
        sprite_entry = self.sprites_yaml_data.get("sprites", {}).get(name, {})
        yaml_frames = sprite_entry.get("frames", [])

        for frame in yaml_frames:
            atlas_id = frame.get("atlas_id", "")
            duration = frame.get("duration_ms", 250)

            # Find this atlas_id region in atlas_data
            image_filename = ""
            x, y, w, h = 0, 0, 32, 32
            found = False

            for img_name, regions in self.sprites_atlas_data.items():
                if isinstance(regions, dict) and atlas_id in regions:
                    region = regions[atlas_id]
                    if isinstance(region, list) and len(region) == 4:
                        image_filename = img_name
                        x, y, w, h = region
                        found = True
                        break

            if not found:
                # Default fallback if the atlas ID doesn't exist in atlas
                image_filename = "test_hero.png"
                x, y, w, h = 0, 0, 32, 32

            frames.append(
                {
                    "atlas_id": atlas_id,
                    "duration": duration,
                    "image": image_filename,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                }
            )

        self.editor.set_sprite_name(name)
        self.editor.load_frames(frames)
        self.preview.sprite_name = name
        self.preview.frames = frames

    def on_frames_changed(self, updated_frames):
        # Dynamically push updated frames to the preview
        self.preview.frames = list(updated_frames)

    def create_sprite(self, instance):
        name = self.new_sprite_input.text.strip()
        if not name:
            return
        if name in self.sprites_yaml_data["sprites"]:
            print(f"Sprite '{name}' already exists.")
            return

        # Add empty sprite
        self.sprites_yaml_data["sprites"][name] = {"frames": []}
        self.new_sprite_input.text = ""
        self.select_sprite(name)

    def delete_sprite(self, instance):
        if not self.selected_sprite:
            return

        # 1. Gather all atlas_ids of this sprite to clean them from atlas too
        sprite_entry = self.sprites_yaml_data["sprites"].get(self.selected_sprite, {})
        atlas_ids_to_remove = {
            f.get("atlas_id")
            for f in sprite_entry.get("frames", [])
            if f.get("atlas_id")
        }

        # 2. Delete from yaml data
        self.sprites_yaml_data["sprites"].pop(self.selected_sprite, None)

        # 3. Clean up corresponding atlas regions
        for img_name, regions in list(self.sprites_atlas_data.items()):
            if isinstance(regions, dict):
                for aid in list(regions.keys()):
                    if aid in atlas_ids_to_remove:
                        regions.pop(aid)
                # If an image has no regions left, optionally remove the image entry
                if not regions:
                    self.sprites_atlas_data.pop(img_name)

        # 4. Save both configurations
        try:
            save_sprites_yaml(self.yaml_path, self.sprites_yaml_data)
            save_sprites_atlas(self.atlas_path, self.sprites_atlas_data)
        except Exception as e:
            print(f"Error saving configurations after deleting sprite: {e}")

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
            # 1. Clean up old atlas mappings for this sprite to prevent leaking orphaned IDs
            old_sprite_entry = self.sprites_yaml_data["sprites"].get(sprite_name, {})
            old_atlas_ids = {
                f.get("atlas_id")
                for f in old_sprite_entry.get("frames", [])
                if f.get("atlas_id")
            }
            for img_name, regions in list(self.sprites_atlas_data.items()):
                if isinstance(regions, dict):
                    for aid in list(regions.keys()):
                        if aid in old_atlas_ids:
                            regions.pop(aid)
                    if not regions:
                        self.sprites_atlas_data.pop(img_name)

            # 2. Re-populate YAML frames representation
            yaml_frames = []
            for frame in frames:
                yaml_frames.append(
                    {"atlas_id": frame["atlas_id"], "duration_ms": frame["duration"]}
                )
            self.sprites_yaml_data["sprites"][sprite_name] = {"frames": yaml_frames}

            # 3. Re-populate Atlas mapping
            for frame in frames:
                image = frame["image"]
                atlas_id = frame["atlas_id"]
                x, y, w, h = frame["x"], frame["y"], frame["w"], frame["h"]

                self.sprites_atlas_data.setdefault(image, {})
                self.sprites_atlas_data[image][atlas_id] = [x, y, w, h]

            # 4. Write back both files
            save_sprites_yaml(self.yaml_path, self.sprites_yaml_data)
            save_sprites_atlas(self.atlas_path, self.sprites_atlas_data)

            print(
                f"Successfully saved sprite '{sprite_name}' to {self.yaml_path} and {self.atlas_path}"
            )
            self.select_sprite(sprite_name)
        except Exception as e:
            print(f"Error saving sprite {sprite_name}: {e}")
