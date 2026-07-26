import sys
from unittest.mock import MagicMock
import types

# Setup mocks for Kivy BEFORE importing anything that uses it
kivy_module = types.ModuleType("kivy")
kivy_uix_module = types.ModuleType("kivy.uix")
kivy_widget_module = types.ModuleType("kivy.uix.widget")
kivy_core_module = types.ModuleType("kivy.core")
kivy_core_image_module = types.ModuleType("kivy.core.image")
kivy_clock_module = types.ModuleType("kivy.clock")
kivy_graphics_module = types.ModuleType("kivy.graphics")


class RealWidget:
    def __init__(self, **kwargs):
        self.canvas = MagicMock()
        self.size = (100, 100)
        self.pos = (0, 0)
        self.children = []

    def add_widget(self, *args, **kwargs):
        pass

    def remove_widget(self, *args, **kwargs):
        pass

    def bind(self, *args, **kwargs):
        pass


kivy_widget_module.Widget = RealWidget
kivy_uix_module.widget = kivy_widget_module
kivy_module.uix = kivy_uix_module
kivy_module.core = kivy_core_module
kivy_core_module.image = kivy_core_image_module
kivy_core_module.graphics = kivy_graphics_module
kivy_module.clock = kivy_clock_module

sys.modules["kivy"] = kivy_module
sys.modules["kivy.uix"] = kivy_uix_module
sys.modules["kivy.uix.widget"] = kivy_widget_module
sys.modules["kivy.core"] = kivy_core_module
sys.modules["kivy.core.image"] = kivy_core_image_module
sys.modules["kivy.clock"] = kivy_clock_module
sys.modules["kivy.graphics"] = kivy_graphics_module

# Mock Kivy components referenced by animated_sprite imports
kivy_graphics_module.Rectangle = MagicMock()
kivy_graphics_module.Color = MagicMock()
kivy_clock_module.Clock = MagicMock()
kivy_clock_module.Clock.schedule_interval = MagicMock()
kivy_core_image_module.Image = MagicMock()

# Now import the class safely
from quick_herbalist.core.animated_sprite import AnimationStateController


def test_controller_initialization():
    frames = [
        {"atlas_id": "frame_0", "duration_ms": 100},
        {"atlas_id": "frame_1", "duration_ms": 200},
    ]
    controller = AnimationStateController(frames)
    assert controller.current_frame_index == 0
    assert controller.current_time == 0.0
    assert controller.frames_data == frames


def test_controller_tick_no_frames():
    controller = AnimationStateController([])
    assert controller.tick(0.1) is False
    assert controller.current_frame_index == 0


def test_controller_tick_advances_index():
    frames = [
        {"atlas_id": "frame_0", "duration_ms": 100},
        {"atlas_id": "frame_1", "duration_ms": 200},
    ]
    controller = AnimationStateController(frames)

    # Tick by 50ms - does not cross 100ms threshold
    changed = controller.tick(0.05)
    assert changed is False
    assert controller.current_frame_index == 0
    assert controller.current_time == 50.0

    # Tick by another 60ms - crosses 100ms threshold (total 110ms)
    changed = controller.tick(0.06)
    assert changed is True
    assert controller.current_frame_index == 1
    assert controller.current_time == 0.0


def test_controller_tick_multi_step_frame_advance():
    frames = [
        {"atlas_id": "frame_0", "duration_ms": 50},
        {"atlas_id": "frame_1", "duration_ms": 50},
        {"atlas_id": "frame_2", "duration_ms": 50},
    ]
    controller = AnimationStateController(frames)

    # Tick by 120ms (crosses frame_0)
    changed = controller.tick(0.12)
    assert changed is True
    assert controller.current_frame_index == 1
    assert controller.current_time == 0.0


def test_controller_set_frames():
    controller = AnimationStateController()
    assert len(controller.frames_data) == 0

    frames = [{"atlas_id": "frame_0", "duration_ms": 100}]
    controller.set_frames(frames)
    assert controller.frames_data == frames
    assert controller.current_frame_index == 0
    assert controller.current_time == 0.0
