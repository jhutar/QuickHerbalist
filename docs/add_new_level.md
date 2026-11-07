# Adding a new level

Levels live in `src/quick_herbalist/assets/levels.yaml`, in play order.
Levels beyond the last entry repeat the last one. Full design rationale:
`docs/multi_level_design.md`.

Schema is strict: unknown keys, missing keys, duplicate names, or a sprite
name not present in `sprites.yaml` are load errors (`LevelConfigError` lists
every problem at once).

## Template

```yaml
  - name: my_level
    background: background_my_level_sprite
    distance: 1200
    start_speed: 4.0
    max_speed: 17.0
    flower:
      sprite: flower_sprite
      interval: 1.0
    stone:
      sprite: stone_sprite
      interval: 3.0
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
  seconds.
- `stone.sprite` / `stone.interval` / `stone.ramp_to` — stone sprite, spawn
  interval in seconds, and the minimum interval to ramp down to over the
  level (omit `ramp_to` to keep the interval constant).

All numbers must be positive.

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
`distance` to make a level harder.
