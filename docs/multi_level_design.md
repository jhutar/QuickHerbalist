# Multi-Level Progression — Design (v2, user-authored levels)

Status: approved draft, not yet implemented. Supersedes the formula-based
`make_level` design (v1).

## Goal

Every level is a hand-authored entry in `levels.yaml` under the player's
control: which sprites appear (background, flower, stone), pacing
(intervals), distance, speed, and per-level stone ramp. Levels the game
doesn't have a definition for: repeat the last level endlessly.

## Level definitions file

Location: `src/quick_herbalist/assets/levels.yaml`, versioned next to
`sprites.yaml`. Hand-edited YAML.

```yaml
# Each entry is one level, in play order.
levels:
  - name: meadow
    background: grass_sprite
    distance: 1000
    start_speed: 3.0
    max_speed: 15.0
    flower:
      sprite: flower_sprite
      interval: 1.0
    stone:
      sprite: stone_sprite
      interval: 3.0
      ramp_to: 0.05

  - name: desert
    background: desert_grass_sprite
    distance: 1400
    start_speed: 3.4
    max_speed: 15.0
    flower:
      sprite: desert_flower_sprite
      interval: 1.2
    stone:
      sprite: desert_stone_sprite
      interval: 2.6
      ramp_to: 0.05
```

### Schema (strict)

| key            | type   | required | meaning                                |
|----------------|--------|----------|----------------------------------------|
| `name`         | str    | yes      | unique human label, shown in HUD       |
| `background`   | str    | yes      | sprite name (cosmetic, tile scroll)    |
| `distance`     | number | yes      | distance to finish the level           |
| `start_speed`  | number | yes      | scroll speed at level start            |
| `max_speed`    | number | yes      | speed cap within the level             |
| `flower`       | map    | yes      | `sprite` (required), `interval` (required, seconds) |
| `stone`        | map    | yes      | `sprite` (required), `interval` (required, starting seconds), `ramp_to` (optional, min interval) |

- Single slot per entity type. One flower type, one stone type per level.
- Frequencies are intervals in seconds (existing convention; lower = harder).
- `stone.ramp_to`: during the level, each spawn shrinks the interval by a
  random step (constant `STONE_RAMP_STEP = 0.05` s) down to `ramp_to`.
  Omit `ramp_to` for a constant-interval (no ramp) level.
- **Strict schema, fail fast and loud.** Any unknown key (top-level in a
  level, or inside `flower`/`stone`), missing required key, wrong type,
  duplicate `name`, or sprite name not present in `sprites.yaml` is a load
  error. All validation errors are collected and reported together,
  e.g. `levels.yaml: level 2 (desert): unknown key 'magnetism_bonuses';
  level 2 (desert): unknown sprite 'desert_floer'`.
- Consequence (accepted): a level file may not contain options for
  mechanics that don't exist yet (e.g. `magnetism_bonuses`). Adding a
  mechanic later is a code + schema change; existing entries don't need
  editing.
- Empty or missing `levels:` list, or a file that is not a mapping with a
  `levels` key: load error.

### Loading

New module `src/quick_herbalist/core/level_config.py` (pure Python, no
Kivy, mirrors `sprite_config.py` structure):

- `LevelDefinition` dataclass: fields per schema, plus `flower`/`stone`
  nested as small dataclasses (`SpawnDefinition(sprite, interval)`,
  `StoneDefinition(sprite, interval, ramp_to: float | None)`).
- `load_levels(path, sprite_names) -> list[LevelDefinition]` — parses and
  validates; raises `LevelConfigError` carrying the full error list.
  `sprite_names` is the set of valid names (from the sprite config), so
  unknown-sprite errors happen at load, not at first spawn.
- `level_for(levels, number) -> LevelDefinition` — 1-based lookup with
  endless-repeat-last: `number > len(levels)` returns the last entry.

Load point: app startup in `app.py`, right after SpriteManager is built.
On `LevelConfigError`: log full error list, show error text, stop the app
before any screen is playable.

### Sprite system

No structural changes. Level definitions reference sprites by the exact
name keys from `sprites.yaml`; SpriteManager lookup stays as is.

One addition: `SpriteManager.names() -> set[str]` (or expose the parsed
config's name set) so `load_levels` can validate against real sprites.

`Background`, `Flower`, `Stone` widgets take their sprite name as a
constructor argument from the level definition instead of hardcoded
`"grass_sprite"` / `"flower_sprite"` / `"stone_sprite"`. Widget sizes stay
hardcoded per type for now (per-level sprite sizing is out of scope).

## Progression flow

- Level number for a run = active character's `levels_completed + 1`
  (`ProfileManager.next_level_number()` helper).
- Win: `complete_level()` persists; next run starts at `levels_completed + 1`
  via the same mechanism. Past the last defined level, every win keeps
  incrementing and `level_for` keeps returning the last definition
  (endless repeat, no hidden difficulty bump).
- Game over: `levels_completed` unchanged, same level restarts.
- Acceptable risk (accepted): inserting or reordering entries in
  `levels.yaml` shifts what `levels_completed: n` points at. Dev-time-only
  concern; restructure = accept save shift.

## Settings migration

`settings.win_distance` and `settings.game_speed_start` in `config.yaml`
become unused — per-level `distance`/`start_speed` replace them. Stop
reading them; existing keys in saved configs are ignored harmlessly.
`settings.fps` unchanged.

## GameRules change

`GameRules.__init__` gains stone pacing: `stone_interval`,
`stone_interval_min` (from `ramp_to`, default = start interval when absent,
i.e. no ramp). New `next_stone_interval()` returns the current interval and
applies the random decay step, clamped to the min. `GameView` uses
`rules.next_stone_interval()` for scheduling; `spawn_stone` no longer
decays manually. Flower spawn period = `level.flower.interval`.

## Affected files

- `src/quick_herbalist/assets/levels.yaml` — new, ships with 2 sample
  levels (meadow = current behavior; desert uses existing sprite names
  as placeholders until real art exists).
- `src/quick_herbalist/core/level_config.py` — new: schema, loader,
  `LevelDefinition`, `level_for`, `LevelConfigError`.
- `src/quick_herbalist/core/sprite_manager.py` — `names()`.
- `src/quick_herbalist/game_rules.py` — stone pacing + `next_stone_interval`.
- `src/quick_herbalist/profiles.py` — `next_level_number()`.
- `src/quick_herbalist/game_scene.py` — `GameView` builds everything from
  `LevelDefinition`; `Background`/`Flower`/`Stone` take sprite names;
  HUD shows `Level: n (name)`.
- `src/quick_herbalist/app.py` — load levels at startup, fail fast.
- `src/quick_herbalist/screens.py` — win screen "Next Level" wording.
- `tests/unit/test_level_config.py` — new: valid load, each validation
  failure class, all-errors-collected, `level_for` repeat-last.
- `tests/unit/test_game_rules.py` — stone ramp: decays, clamps at
  `ramp_to`, no ramp when absent.
- `tests/unit/test_profiles.py` — `next_level_number`.
- `tests/unit/test_game_scene_widgets.py` — GameView uses level sprite
  names for background/flower/stone.

## Open questions

1. Ship a 2nd sample level now (desert, placeholder sprites) or ship
   only `meadow` until real sprites exist? Strict sprite validation means
   the desert entry can only reference names that already exist in
   `sprites.yaml`.
2. Per-level sprite *sizes* (a big desert cactus flower?) — deferred,
   widget sizes stay per-type constants.
