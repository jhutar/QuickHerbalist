from kivy.uix.boxlayout import BoxLayout
from .preview import SpritePreviewWidget
from .sequence_editor import SequenceEditorWidget

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
        self.editor = SequenceEditorWidget()
        self.add_widget(self.editor)

    def set_sprite_data(self, sprite_name, texture, frames):
        """
        Updates both the preview and the sequence editor with the provided data.
        """
        self.preview.sprite_name = sprite_name
        self.preview.set_texture(texture)
        self.preview.frames = frames
        self.editor.frames = frames
        self.editor.refresh_rv()
