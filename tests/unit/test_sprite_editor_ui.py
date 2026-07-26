import sys
import json
import yaml
import pytest
from unittest.mock import MagicMock, patch


# 1. Setup descriptor properties to mock Kivy properties before importing UI elements
class MockProperty:
    def __init__(self, default=None):
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
        on_cb = getattr(instance, f"on_{self.name}", None)
        if on_cb:
            on_cb(instance, value)

    def __set_name__(self, owner, name):
        self.name = name


class NumericProperty(MockProperty):
    pass


class ObjectProperty(MockProperty):
    pass


class ListProperty(MockProperty):
    def __init__(self, default=None):
        super().__init__(default if default is not None else [])


class StringProperty(MockProperty):
    def __init__(self, default=""):
        super().__init__(default)


class MockWidget:
    def __init__(self, **kwargs):
        self.children = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add_widget(self, widget, *args, **kwargs):
        self.children.append(widget)

    def remove_widget(self, widget, *args, **kwargs):
        if widget in self.children:
            self.children.remove(widget)

    def clear_widgets(self):
        self.children.clear()

    def bind(self, **kwargs):
        pass

    def setter(self, name):
        return lambda instance, value: None


class BoxLayout(MockWidget):
    pass


class GridLayout(MockWidget):
    pass


class ScrollView(MockWidget):
    pass


class Label(MockWidget):
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text


class Button(MockWidget):
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text


class TextInput(MockWidget):
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text


class Image(MockWidget):
    pass


class Popup(MockWidget):
    pass


class App(MockWidget):
    pass


class MockClock:
    @staticmethod
    def schedule_interval(callback, interval):
        pass


class MockCoreImage:
    def __init__(self, filename):
        self.texture = MagicMock()
        self.texture.size = (256, 256)


# Inject mocks into sys.modules
sys.modules["kivy"] = MagicMock()
sys.modules["kivy.properties"] = MagicMock()
sys.modules["kivy.properties"].NumericProperty = NumericProperty
sys.modules["kivy.properties"].ObjectProperty = ObjectProperty
sys.modules["kivy.properties"].ListProperty = ListProperty
sys.modules["kivy.properties"].StringProperty = StringProperty

sys.modules["kivy.uix"] = MagicMock()
sys.modules["kivy.uix.boxlayout"] = MagicMock()
sys.modules["kivy.uix.boxlayout"].BoxLayout = BoxLayout

sys.modules["kivy.uix.gridlayout"] = MagicMock()
sys.modules["kivy.uix.gridlayout"].GridLayout = GridLayout

sys.modules["kivy.uix.scrollview"] = MagicMock()
sys.modules["kivy.uix.scrollview"].ScrollView = ScrollView

sys.modules["kivy.uix.label"] = MagicMock()
sys.modules["kivy.uix.label"].Label = Label

sys.modules["kivy.uix.button"] = MagicMock()
sys.modules["kivy.uix.button"].Button = Button

sys.modules["kivy.uix.textinput"] = MagicMock()
sys.modules["kivy.uix.textinput"].TextInput = TextInput

sys.modules["kivy.uix.image"] = MagicMock()
sys.modules["kivy.uix.image"].Image = Image

sys.modules["kivy.uix.popup"] = MagicMock()
sys.modules["kivy.uix.popup"].Popup = Popup

sys.modules["kivy.uix.filechooser"] = MagicMock()
sys.modules["kivy.uix.filechooser"].FileChooserListView = MockWidget

sys.modules["kivy.app"] = MagicMock()
sys.modules["kivy.app"].App = App

sys.modules["kivy.clock"] = MagicMock()
sys.modules["kivy.clock"].Clock = MockClock

sys.modules["kivy.core"] = MagicMock()
sys.modules["kivy.core.image"] = MagicMock()
sys.modules["kivy.core.image"].Image = MockCoreImage


# 2. Import components under test now that mocks are active
from quick_herbalist.tools.sprite_editor.ui.main_layout import SpriteEditorMainLayout  # noqa: E402
from quick_herbalist.tools.sprite_editor.ui.sequence_editor import SequenceEditorWidget  # noqa: E402


@pytest.fixture
def mock_get_asset_path(tmp_path):
    # Mock get_asset_path to point to tmp_path files
    yaml_file = tmp_path / "sprites.yaml"
    atlas_file = tmp_path / "sprites.atlas"
    yaml_file.write_text(
        """
sprites:
  hero_run:
    frames:
      - atlas_id: frame_0
        duration_ms: 100
""",
        encoding="utf-8",
    )
    atlas_file.write_text(
        """
{
  "hero.png": {
    "frame_0": [0, 0, 32, 32]
  }
}
""",
        encoding="utf-8",
    )
    return str(yaml_file), str(atlas_file)


def test_main_layout_load_and_select_sprite(mock_get_asset_path):
    yaml_path, atlas_path = mock_get_asset_path
    with patch(
        "quick_herbalist.tools.sprite_editor.ui.main_layout.get_asset_path"
    ) as mock_gap:
        mock_gap.side_effect = lambda filename: (
            yaml_path if "yaml" in filename else atlas_path
        )

        layout = SpriteEditorMainLayout()

        # Verify initial loaded state
        assert "hero_run" in layout.stitcher.sprites_yaml_data["sprites"]

        # Select sprite
        layout.select_sprite("hero_run")
        assert layout.selected_sprite == "hero_run"

        # Verify editor loaded frames correctly
        assert len(layout.editor.frames) == 1
        assert layout.editor.frames[0]["atlas_id"] == "frame_0"
        assert layout.editor.frames[0]["duration"] == 100
        assert layout.editor.frames[0]["image"] == "hero.png"
        assert layout.editor.frames[0]["x"] == 0
        assert layout.editor.frames[0]["y"] == 0
        assert layout.editor.frames[0]["w"] == 32
        assert layout.editor.frames[0]["h"] == 32


def test_sequence_editor_add_frame_auto_advance(mock_get_asset_path):
    # Rule 4: Selected frame auto-advance on add frame
    editor = SequenceEditorWidget()
    editor.set_sprite_name("hero_run")

    initial_frames = [
        {
            "atlas_id": "frame_0",
            "duration": 100,
            "image": "hero.png",
            "x": 10,
            "y": 20,
            "w": 32,
            "h": 64,
        }
    ]
    editor.load_frames(initial_frames)

    # Select the first frame
    editor.select_frame(0)

    # Add frame
    editor.add_frame(None)

    # Assert second frame is added and auto-advanced
    assert len(editor.frames) == 2
    new_frame = editor.frames[1]
    assert new_frame["image"] == "hero.png"
    assert new_frame["duration"] == 100
    assert new_frame["x"] == 10 + 32  # Advanced by width
    assert new_frame["y"] == 20
    assert new_frame["w"] == 32
    assert new_frame["h"] == 64


def test_main_layout_create_and_delete_sprite(mock_get_asset_path):
    yaml_path, atlas_path = mock_get_asset_path
    with patch(
        "quick_herbalist.tools.sprite_editor.ui.main_layout.get_asset_path"
    ) as mock_gap:
        mock_gap.side_effect = lambda filename: (
            yaml_path if "yaml" in filename else atlas_path
        )

        layout = SpriteEditorMainLayout()

        # Create new sprite
        layout.new_sprite_input.text = "new_sprite"
        layout.create_sprite(None)

        assert "new_sprite" in layout.stitcher.sprites_yaml_data["sprites"]
        assert layout.selected_sprite == "new_sprite"

        # Delete selected sprite
        layout.delete_sprite(None)
        assert "new_sprite" not in layout.stitcher.sprites_yaml_data["sprites"]
        assert layout.selected_sprite == ""


def test_main_layout_save_sprite(mock_get_asset_path):
    yaml_path, atlas_path = mock_get_asset_path
    with patch(
        "quick_herbalist.tools.sprite_editor.ui.main_layout.get_asset_path"
    ) as mock_gap:
        mock_gap.side_effect = lambda filename: (
            yaml_path if "yaml" in filename else atlas_path
        )

        layout = SpriteEditorMainLayout()
        layout.select_sprite("hero_run")

        # Modify and add frame in sequence editor
        layout.editor.frames.append(
            {
                "atlas_id": "frame_1",
                "duration": 150,
                "image": "hero.png",
                "x": 32,
                "y": 0,
                "w": 32,
                "h": 32,
            }
        )

        # Trigger save
        layout.on_save_callback("hero_run", layout.editor.frames)

        # Read back from yaml and atlas to confirm
        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)
        with open(atlas_path, "r") as f:
            atlas_data = json.load(f)

        assert "hero_run" in yaml_data["sprites"]
        frames = yaml_data["sprites"]["hero_run"]["frames"]
        assert len(frames) == 2
        assert frames[1]["atlas_id"] == "frame_1"
        assert frames[1]["duration_ms"] == 150

        assert "hero.png" in atlas_data
        assert "frame_1" in atlas_data["hero.png"]
        assert atlas_data["hero.png"]["frame_1"] == [32, 0, 32, 32]


def test_save_button_triggers_on_save_callback(mock_get_asset_path):
    yaml_path, atlas_path = mock_get_asset_path
    with patch(
        "quick_herbalist.tools.sprite_editor.ui.main_layout.get_asset_path"
    ) as mock_gap:
        mock_gap.side_effect = lambda filename: (
            yaml_path if "yaml" in filename else atlas_path
        )

        layout = SpriteEditorMainLayout()
        layout.select_sprite("hero_run")

        # Modify frames
        layout.editor.frames = [
            {
                "atlas_id": "frame_0",
                "duration": 500,
                "image": "hero.png",
                "x": 0,
                "y": 0,
                "w": 32,
                "h": 32,
            }
        ]

        # Trigger button save
        layout.editor.save_sequence(None)

        # Read back from yaml and atlas to confirm
        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)
        with open(atlas_path, "r") as f:
            atlas_data = json.load(f)

        assert yaml_data["sprites"]["hero_run"]["frames"][0]["duration_ms"] == 500
        assert atlas_data["hero.png"]["frame_0"] == [0, 0, 32, 32]


def test_sequence_editor_reorder_frames():
    editor = SequenceEditorWidget()
    editor.set_sprite_name("hero_run")

    initial_frames = [
        {
            "atlas_id": "frame_0",
            "duration": 100,
            "image": "hero.png",
            "x": 0,
            "y": 0,
            "w": 32,
            "h": 32,
        },
        {
            "atlas_id": "frame_1",
            "duration": 200,
            "image": "hero.png",
            "x": 32,
            "y": 0,
            "w": 32,
            "h": 32,
        },
        {
            "atlas_id": "frame_2",
            "duration": 300,
            "image": "hero.png",
            "x": 64,
            "y": 0,
            "w": 32,
            "h": 32,
        },
    ]
    editor.load_frames(initial_frames)
    assert len(editor.frames) == 3

    # Move index 1 (frame_1) up
    editor.move_frame_up(1)
    assert editor.frames[0]["atlas_id"] == "frame_1"
    assert editor.frames[1]["atlas_id"] == "frame_0"

    # Move index 1 (now frame_0) down
    editor.move_frame_down(1)
    assert editor.frames[1]["atlas_id"] == "frame_2"
    assert editor.frames[2]["atlas_id"] == "frame_0"
