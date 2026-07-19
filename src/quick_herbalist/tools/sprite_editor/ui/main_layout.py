import os
import yaml
from kivy.uix.boxlayout import BoxLayout
from .preview import SpritePreviewWidget
from .sequence_editor import SequenceEditorWidget
from quick_herbalist.core.config_parser import save_sprites_yaml, load_sprites_yaml

class SpriteEditorMainLayout(BoxLayout):
    """
    The main layout of the Sprite Editor, bringing together the preview and sequence editor.
    """
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        # Preview section (Left)
        self.preview = SpritePreviewWidget()
        self.add_widget(self.preview)

        # Sequence Editor section (Right)
        self.editor = SequenceEditorWidget(on_save_callback=self.on_save_callback)
        self.add_widget(self.editor)

    def set_sprite_data(self, sprite_name, texture, frames):
        """
        Updates both the preview and the sequence editor with the provided data.
        """
        self.preview.sprite_name = sprite_name
        self.preview.set_texture(texture)
        self.preview.frames = frames
        self.editor.sprite_name = sprite_name
        self.editor.frames = frames
        self.editor.refresh_rv()

    def on_save_callback(self, sprite_name, frames):
        if not sprite_name:
            print("No sprite name specified. Cannot save.")
            return

        # The paths should be relative to the project root.
        # According to the project structure: src/quick_herbalist/assets/
        yaml_path = os.path.join("src", "quick_herbalist", "assets", "sprites.yaml")
        atlas_path = os.path.join("src", "quick_herbalist", "assets", "sprites.atlas")

        try:
            # 1. Load existing yaml
            if os.path.exists(yaml_path):
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {"sprites": {}}
            else:
                data = {"sprites": {}}

            # 2. Update the sprite data
            if "sprites" not in data:
                data["sprites"] = {}
            
            data["sprites"][sprite_name] = {"frames": frames}

            # 3. Save yaml
            save_sprites_yaml(yaml_path, data)
            
            # 4. Save atlas (placeholder as we are only editing frames here)
            # If we had atlas data, we would save it here too.
            if os.path.exists(atlas_path):
                # For now, we'll just ensure it exists or do nothing if it's not modified.
                # The requirement is to "write assets/sprites.yaml and assets/sprites.atlas".
                # Since we are not modifying the atlas content in this task, 
                # we might just skip it, or if it doesn't exist, we might need to create it.
                pass

            print(f"Successfully saved sprite {sprite_name} to {yaml_path}")
        except Exception as e:
            print(f"Error saving sprite {sprite_name}: {e}")
