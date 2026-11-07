# Multi-Level Progression — Design Draft

Status: draft, not yet implemented.

## Goal

Character who finishes a level continues on a harder next level: longer
distance, faster start, denser stones, more stones in flight at once.
Per-character level number is already persisted (`levels_completed` in the
profile), so progression state exists; what is missing is *level-scoped game
parameters* and *flow* (win -> next level, not same level).

## Current state (baseline)

- `GameRules(win_distance, start_speed, max_speed)` — params pulled from global
  `profile_manager.settings`, identical every run.
- Stone/flower spawn rates hardcoded in `GameView` (`stone_interval = 3.0`,
  flower every 1.0 s).
- `GameWonScreen.restart_game` re-enters the `game` screen; the new
  `GameView` is built with the same params, so "Play Again" replays level 1.
- `profile.complete_level()` already increments `levels_completed`.

## Design

### 1. `LevelConfig` (new, in `game_rules.py` or sibling module)

Plain dataclass describing one level's difficulty. No Kivy imports, pure
Python, testable headless — same rule as `GameRules`.

```
LevelConfig(
    level: int,          # 1-based
    win_distance: float, # distance required to finish
    start_speed: float,
    max_speed: float,
    stone_interval: float,   # base seconds between stone spawns
    stone_interval_min: float, # how far the interval may shrink in-level
    stone_interval_decay: float, # per-spawn interval reduction
    flower_interval: float,
)
```

`GameRules.__init__` gains an optional `LevelConfig` (or its fields) so
stone pacing rules live in the rules layer, not in `GameView`. `GameView`
keeps only spawning/scheduling.

### 2. Level generation: formula first, explicit levels later

Default: a `make_level(n) -> LevelConfig` pure function that scales by level
number. No data files, no design work for levels 2..∞.

Proposed curve (tunables in one place):

| param            | formula (n = level)                  | L1      | L2     | L5     |
|------------------|--------------------------------------|---------|--------|--------|
| win_distance     | `1000 * 1.25 ** (n-1)`               | 1000    | 1250   | 2441   |
| start_speed      | `min(3.0 + 0.4 * (n-1), 7.0)`        | 3.0     | 3.4    | 4.6    |
| max_speed        | `min(15.0, start_speed + 9.0)`       | 15.0    | 15.0   | 15.0   |
| stone_interval   | `max(3.0 * 0.9 ** (n-1), 0.8)`       | 3.0     | 2.7    | 2.19   |
| flower_interval  | fixed `1.0`                          | 1.0     | 1.0    | 1.0    |

Later levels can add content hooks to `LevelConfig` without breaking the
function (all optional, sensible defaults): `extra_stone_chance` (spawn a
second stone in the same row band), `hazard: str | None` (new obstacle type
name from sprite config). Keep off until the base curve plays well.

Extension point: if a handcrafted level list is ever wanted, read an
optional `levels:` YAML section (list of per-level overrides) and let
`make_level` apply an override on top of the formula for known numbers.
Formula stays the fallback for anything beyond the list. Do not build this
until it is actually needed.

### 3. Which level is played

- Level number = `active character's levels_completed + 1`. Single source of
  truth; no extra persistence.
- `GameView` computes it once in `__init__` via the profile manager:
  `profile_manager.next_level_number()` (thin helper returning
  `levels_completed + 1` for the active character, `1` when none).
- HUD: extend `char_label` line (or new small label) to show `Level: n`.

### 4. Flow changes

- **Win** (`game_won`): `complete_level()` already runs and persists.
  `GameWonScreen` then shows "Next Level" (reworded from "Play Again") and
  its handler re-enters the `game` screen; the fresh `GameView` reads the now
  incremented `levels_completed` and starts level n+1. No explicit level
  passing between screens — the profile is the carrier.
- **Game over** (`game_over`): "Play Again" re-enters `game`; `levels_completed`
  unchanged, so the same level restarts. No code change needed beyond the
  shared mechanism.
- **Restart from menu**: also starts at `levels_completed + 1`. Consistent:
  you are always "about to play your next level".

Edge case: character with 0 levels completed -> level 1, identical to today's
behavior with the L1 formula values matching current defaults
(`win_distance` 1000, `start_speed` 3.0). Existing `settings` keys
`win_distance`/`game_speed_start` remain as *level-1 base* values read by
`make_level`, so existing configs still honor user tuning.

### 5. Affected files

- `src/quick_herbalist/game_rules.py` — `LevelConfig`, `make_level`,
  `GameRules` takes level pacing params.
- `src/quick_herbalist/profiles.py` — `next_level_number()` helper.
- `src/quick_herbalist/game_scene.py` — `GameView` builds rules from
  `make_level(next_level_number)`; stone/flower spawn intervals sourced from
  `LevelConfig`; HUD level label.
- `src/quick_herbalist/screens.py` — `GameWonScreen` copy ("Next Level").
- `tests/unit/` — new `test_make_level.py` (curve monotonicity, L1 == old
  defaults, clamps), stone-interval rules tests, `next_level_number` tests.

## Open questions

1. Does "Play Again" after a *win* mean continue (next level) or repeat?
   Draft assumes continue; repeating a level would need an explicit "Replay"
   button and a level override in flow — small addition if wanted.
2. Distance pacing: multiplicative (1.25x) or additive (+250 per level)?
   Multiplicative chosen — keeps late levels interesting; one-line change.
3. Should `max_speed` stay 15 for all levels or rise after some level?
   Draft holds it at 15; revisit once level 5+ feels flat.
