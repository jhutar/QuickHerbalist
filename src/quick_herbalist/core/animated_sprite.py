from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage


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

        self.current_frame_index = 0
        self.current_time = 0.0

        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size)

        self._load_frame(0)
        self._event = Clock.schedule_interval(self.update, 0.01)

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

        core_img = CoreImage(img_name)
        self.rect.texture = core_img.texture.get_region(
            region[0], region[1], region[2], region[3]
        )
        self.rect.size = (region[2], region[3])

    def update(self, dt):
        self.current_time += dt * 1000
        frame_info = self.frames_data[self.current_frame_index]
        duration = frame_info.get("duration_ms", 100)

        if self.current_time >= duration:
            self.current_time = 0
            self.current_frame_index = (self.current_frame_index + 1) % len(
                self.frames_data
            )
            self._load_frame(self.current_frame_index)
