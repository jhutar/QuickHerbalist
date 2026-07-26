from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage


class AnimationStateController:
    """
    A Kivy-free, pure Python animation state model.
    Manages active frame index, accumulated delta-time, frame-level durations,
    and frame transitions in isolation.
    """

    def __init__(self, frames_data: list[dict] = None):
        self.frames_data = frames_data or []
        self.current_frame_index = 0
        self.current_time = 0.0  # in ms

    def set_frames(self, frames_data: list[dict]):
        self.frames_data = frames_data or []
        self.current_frame_index = 0
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
            self.current_frame_index = (self.current_frame_index + 1) % len(
                self.frames_data
            )
            return True

        return False


class AnimatedSprite(Widget):
    def __init__(self, sprite_name, sprites_data, atlas_data, **kwargs):
        super().__init__(**kwargs)
        self.sprite_name = sprite_name
        self.sprites_data = sprites_data
        self.atlas_data = atlas_data

        self.frames_data = (
            sprites_data.get("sprites", {}).get(sprite_name, {}).get("frames", [])
        )
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
        self.rect.pos = self.pos

    def _load_frame(self, index):
        frame_info = self.frames_data[index]
        atlas_id = frame_info["atlas_id"]

        img_name = None
        region = None

        for name, regions in self.atlas_data.items():
            if atlas_id in regions:
                img_name = name
                region = regions[atlas_id]
                break

        if img_name is None or region is None:
            raise ValueError(f"Atlas ID '{atlas_id}' not found")

        from quick_herbalist.core.config_parser import get_asset_path

        core_img = CoreImage(get_asset_path(img_name))
        self.rect.texture = core_img.texture.get_region(
            region[0], region[1], region[2], region[3]
        )
        self.size = (region[2], region[3])
        self.rect.size = self.size

    def update(self, dt):
        if self.controller.tick(dt):
            self._load_frame(self.controller.current_frame_index)
