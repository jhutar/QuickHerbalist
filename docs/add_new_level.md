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
    entities:
      - type: flower
        sprite: dandelion_sprite
        interval: 0.7
      - type: stone
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
- `entities` — non-empty list of what spawns in the level, one item per
  entity type instance:
  - `type` — entity kind, must be a registered name
    (`ENTITY_TYPES` in `src/quick_herbalist/game/entities.py`:
    currently `flower`, `stone`).
  - `sprite` — sprite name to render.
  - `interval` — spawn interval in seconds.
  - `ramp_to` (optional) — floor the interval ramps down to: each spawn
    shrinks the interval by a random 0–0.05 s (`RAMP_STEP` in
    `game/scene.py`) down to that floor (omit to keep it constant).

The same `type` may appear twice with different sprites (e.g. two flower
varieties); each entry spawns independently. A collected entity's sprite
name is what lands in the inventory harvest (see
`docs/add_new_potion.md`).

All numbers must be positive.

Sprite *sizes* are per-type class constants (`SIZE` on the entity class);
per-level sizing is not supported.

## Steps

1. Add the background sprite (and any new entity sprites) first, per
   `docs/add_new_sprite.md`.
2. Append the level entry at the end of `levels.yaml` (play order = list
   order).
3. Verify the file loads, e.g.:

   ```python
   from quick_herbalist.core.level_config import load_levels
   load_levels("src/quick_herbalist/assets/levels.yaml",
               {"background_my_level_sprite", "dandelion_sprite", "stone_sprite"})
   ```

   The real game validates against all sprites in `sprites.yaml`.

## Adding a new entity type

The scene is generic over entity types; behavior lives in one class per
type. A new type (bigger rocks, chasing spiders, slowing hills, ...) is:

1. A `GameEntity` subclass in `src/quick_herbalist/game/entities.py`
   overriding only what it needs:
   - `SIZE` — render size (bigger rocks: just a larger `SIZE`, e.g. a
     `Rock(Stone)` with `SIZE = (96, 128)`).
   - `SPAWN_X_MIN` / `SPAWN_X_MAX` — horizontal spawn window past the right
     edge; `random_spawn_y()` — vertical placement (full-height pillars
     override it to return `0`).
   - `move(frame)` — per-frame motion (default: scroll left with the
     world; a spider scrolls and steers toward `frame.hero`).
   - `on_enter(frame)` — one-shot reaction when the hero starts
     overlapping it (collect: `frame.rules.on_collected(self.sprite_name)`
     + `self.done = True`; damage: `frame.rules.on_damaged()` +
     `self.done = True`).
   - `hero_speed_factor()` — hero movement multiplier while overlapping
     (a hill returns e.g. `0.5`).
   - `MAGNETIC = True` — pulled by the magnetism potion (flowers set it).
2. One entry in `ENTITY_TYPES` mapping its `type` name to the class.
3. A test in `tests/unit/test_game_scene.py` proving the behavior via a
   subclass (see `test_chasing_entity_follows_hero_and_damages` and
   `test_slowing_entity_halves_hero_step_while_overlapping`).
4. Entity instances in `levels.yaml` (above) — only levels that list the
   type spawn it.

The scene (`game/scene.py`) spawns, moves, overlap-checks, and culls every
registered type the same way; it needs no changes for a new type.

## Tuning

Keep the difficulty ramp monotonic: each level should be at least as long,
fast, and dense as the one before it. Lower `start_speed`/`interval` or raise
`distance` to make a level harder. Compare against the last shipped entry
in `levels.yaml`, not the template — the template values are a starting
guess.
