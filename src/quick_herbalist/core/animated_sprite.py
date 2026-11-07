from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget


class AnimationStateController:
    """
    A Kivy-free, pure Python animation state model.
    Manages active frame index, accumulated delta-time, frame-level durations,
    and frame transitions in isolation.
    """

    def __init__(self, frames_data: list[dict] = None):
        """Initialize with optional frames data and reset animation state."""
        self.frames_data = frames_data or []
        self.current_frame_index = 0
        self.current_time = 0.0  # in ms

    def set_frames(self, frames_data: list[dict]):
        """Replace current frames and reset animation state."""
        self.frames_data = frames_data or []
        self.current_frame_index = 0
        self.current_time = 0.0

    def reset_time(self):
        """Reset accumulated time without changing the frame index."""
        self.current_time = 0.0

    def tick(self, dt: float) -> bool:
        """
        Advances animation time by dt (in seconds).
        Returns True if the active frame index changed, False otherwise.
        """
        if not self.frames_data:
            return False

        # Convert delta-time from seconds to milliseconds
        self.current_time += dt * 1000.0
        frame_info = self.frames_data[self.current_frame_index % len(self.frames_data)]
        duration = frame_info.get("duration_ms", 100)

        if self.current_time >= duration:
            self.current_time = 0.0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames_data)
            return True

        return False


class AnimatedSprite(Widget):
    """Widget that renders an animated sprite from resolved frame dicts."""

    def __init__(self, sprite_name, frames_data, **kwargs):
        """Create widget with sprite name and resolved frame dicts.

        Each frame dict: {atlas_id, image, x, y, w, h, duration_ms}.
        """
        super().__init__(**kwargs)
        self.sprite_name = sprite_name
        self.frames_data = frames_data or []
        if not self.frames_data:
            raise ValueError(f"No frames for sprite '{sprite_name}'")

        # Delegate clock-ticks and time progression to the AnimationStateController
        self.controller = AnimationStateController(self.frames_data)

        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect)
        self._load_frame(0)
        self._event = Clock.schedule_interval(self.update, 0.01)

    @property
    def current_frame_index(self):
        return self.controller.current_frame_index

    @property
    def current_time(self):
        return self.controller.current_time

    def update_rect(self, *args):
        """Keep the texture rectangle synced with widget position."""
        self.rect.pos = self.pos

    def _load_frame(self, index):
        """Load frame texture from the resolved region and update widget size."""
        from quick_herbalist.core.config_parser import get_asset_path

        frame_info = self.frames_data[index]
        core_img = CoreImage(get_asset_path(frame_info["image"]))
        self.rect.texture = core_img.texture.get_region(
            frame_info["x"], frame_info["y"], frame_info["w"], frame_info["h"]
        )
        self.size = (frame_info["w"], frame_info["h"])
        self.rect.size = self.size

    def update(self, dt):
        """Clock callback that ticks the controller and reloads frame on change."""
        if self.controller.tick(dt):
            self._load_frame(self.controller.current_frame_index)
