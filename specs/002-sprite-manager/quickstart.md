# Quickstart: Sprite Manager Validation

This guide provides runnable validation scenarios to prove the Sprite Manager feature works end-to-end once implemented.

## Prerequisites
- Python environment configured with `uv`.
- Project dependencies installed.
- A test image `assets/test_hero.png` exists (at least 64x32 pixels).

## Scenario 1: Standalone GUI Integrity Check

**Setup:**
Create dummy configuration files:

`assets/sprites.yaml`
```yaml
sprites:
  test_sprite:
    frames:
      - atlas_id: "test_frame_0"
        duration_ms: 250
      - atlas_id: "missing_frame_1" # This ID will not exist in the atlas
        duration_ms: 250
```

`assets/sprites.atlas`
```json
{
  "test_hero.png": {
    "test_frame_0": [0, 0, 32, 32]
  }
}
```

**Run Command:**
```bash
uv run manage-sprites
```

**Expected Outcome:**
The GUI application launches and immediately displays a warning or logs an error indicating that `missing_frame_1` referenced in `sprites.yaml` is not found in `sprites.atlas`.

## Scenario 2: Requesting an Animated Sprite in Game

**Setup:**
Fix the configuration files so they are valid.

`assets/sprites.yaml`
```yaml
sprites:
  test_sprite:
    frames:
      - atlas_id: "test_frame_0"
        duration_ms: 1000
      - atlas_id: "test_frame_1"
        duration_ms: 1000
```

`assets/sprites.atlas`
```json
{
  "test_hero.png": {
    "test_frame_0": [0, 0, 32, 32],
    "test_frame_1": [32, 0, 32, 32]
  }
}
```

**Run Command:**
Create a simple `test_sprite.py` in the root:
```python
from kivy.app import App
from quick_herbalist.core.sprite_manager import SpriteManager

class TestApp(App):
    def build(self):
        # The SpriteManager loads assets/sprites.yaml by default
        sm = SpriteManager()
        return sm.get('test_sprite')

if __name__ == '__main__':
    TestApp().run()
```

```bash
uv run python test_sprite.py
```

**Expected Outcome:**
A Kivy window opens displaying the sprite. The sprite should autonomously toggle between the two 32x32 regions defined in `test_hero.png` every 1 second (1000ms).