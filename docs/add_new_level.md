# Adding a new level

Levels live in `src/quick_herbalist/assets/levels.yaml`, in play order.
A run plays level `levels_completed + 1` of the active character: a win
persists the completion, a game over restarts the same level. Levels
beyond the last entry repeat the last one endlessly (no hidden difficulty
bump).

Only append new entries at the end. Inserting or reordering shifts what a
player's saved `levels_completed: n` points at.

Schema is strict: unknown keys, missing keys, duplicate names, or a sprite
name not present in `sprites.yaml` are load errors (`LevelConfigError` lists
every problem at once).

## Template

```yaml
  - name: my_level
    background: background_my_level_sprite
    distance: 320
    start_speed: 6.0
    max_speed: 20.0
    flower:
      sprite: flower_sprite
      interval: 0.7
    stone:
      sprite: stone_sprite
      interval: 1.8
      ramp_to: 0.05
```

## Fields

- `name` — unique, human-readable level id.
- `background` — sprite name of the tiling background (see
  `docs/add_new_sprite.md`).
- `distance` — length of the level in pixels.
- `start_speed` / `max_speed` — scroll speed in pixels/frame at level start
  and at level end.
- `flower.sprite` / `flower.interval` — flower sprite and spawn interval in
  seconds. The flower type is also the only source of potion brewing
  ingredients (see `docs/add_new_potion.md`).
- `stone.sprite` / `stone.interval` / `stone.ramp_to` — stone sprite, spawn
  interval in seconds, and the floor the interval ramps down to: each spawn
  shrinks the interval by a random 0–0.05 s (`STONE_RAMP_STEP` in
  `game_rules.py`) down to that floor (omit `ramp_to` to keep the interval
  constant).

All numbers must be positive.

Sprite *sizes* are per-type widget constants; per-level sizing is not
supported.

## Steps

1. Add the background sprite (and any new flower/stone sprites) first, per
   `docs/add_new_sprite.md`.
2. Append the level entry at the end of `levels.yaml` (play order = list
   order).
3. Verify the file loads, e.g.:

   ```python
   from quick_herbalist.core.level_config import load_levels
   load_levels("src/quick_herbalist/assets/levels.yaml",
               {"background_my_level_sprite", "flower_sprite", "stone_sprite"})
   ```

   The real game validates against all sprites in `sprites.yaml`.

## Tuning

Keep the difficulty ramp monotonic: each level should be at least as long,
fast, and dense as the one before it. Lower `start_speed`/`interval` or raise
`distance` to make a level harder. Compare against the last shipped entry
in `levels.yaml`, not the template — the template values are a starting
guess.
