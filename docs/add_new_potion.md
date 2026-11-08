# Adding a new potion

A potion is three independent pieces:

1. A **recipe** in `src/quick_herbalist/assets/recipes.yaml` (required).
2. **Translations** for its name and description (required).
3. An **in-run effect** in `src/quick_herbalist/game/effects.py` (optional —
   a potion without one is consumed on use but does nothing).

## How potions flow through the game

- Runs collect flowers; on win, `rules.score` flowers of the level's
  `flower.sprite` go to the character inventory (`profiles.add_flowers`).
  **An ingredient is only obtainable if some level drops that sprite as its
  flower** — new flower types come from `docs/add_new_sprite.md` (the
  sprite) + `docs/add_new_level.md` (a level that drops it), not from the
  recipe file.
- Potion screen (`screens/potions_screen.py`): drag inventory ingredients
  into the cauldron, drag the spoon onto the cauldron to mix. Mixing matches
  the cauldron contents against recipes via `match_recipe` (exact,
  order-independent multiset equality — extra, missing, or over-counted
  ingredients fail). A match adds one potion of `recipe.id` to the character;
  a non-match **wastes the ingredients forever**.
- The player drags brewed potions into the 3 run slots
  (`RUN_SLOT_COUNT` in `potions.py`). Clicking a slot returns the potion.
- In a run, keys `1`/`2`/`3` use the slot: the potion is consumed
  (`use_run_slot`, lost for good) and its effect runs for
  `recipe.duration_seconds` seconds. Effects stack per activation and show
  on the HUD as "<potion name> <whole seconds left>".

## 1. Recipe

Append to `recipes.yaml`:

```yaml
  - id: potion_speed
    name_key: potion_speed_name
    description_key: potion_speed_description
    ingredients:
      flower_sprite: 3
    duration_seconds: 15
```

Fields (validated in `potions.py:load_recipes`, fails fast on first error):

- `id` — unique, used everywhere else (effect registry, save data,
  translation key suffix).
- `name_key` / `description_key` — gettext msgids shown in the recipe book
  and HUD.
- `ingredients` — non-empty mapping of sprite name -> positive int count.
  Sprite names must exist in `sprites.yaml` (unknown = load error at
  startup).
- `duration_seconds` — positive number, the effect duration in seconds.

Note: unlike `levels.yaml`, the recipe loader does **not** reject unknown
extra keys — keep entries clean anyway.

The UI needs no changes: recipe book, ingredient chips, potion chips, and
run slots are all generated from the loaded recipes and save data.

## 2. Translations

Add both keys to `locales/en/LC_MESSAGES/base.po`,
`locales/cs/LC_MESSAGES/base.po`, and `locales/base.pot`, then recompile
with `python scripts/compile_mo.py` (the pre-commit `compile .po -> .mo`
hook also does this; commit the regenerated `.mo` files together):

```
msgid "potion_speed_name"
msgstr "Speed Potion"

msgid "potion_speed_description"
msgstr "..."
```

If the recipe uses a **new ingredient sprite**, it is a level flower and
needs a display-name entry in the same catalogs — see the "Flower sprites"
section of `docs/add_new_sprite.md` (the recipe book renders ingredient
lines with `_(sprite_name)`). All potion icons are the `star.png`
placeholder — no per-potion art exists.

## 3. In-run effect (optional)

In `src/quick_herbalist/game/effects.py`:

```python
class SpeedEffect(RunEffect):
    """Double scroll speed growth while active (example, not real)."""

    def __init__(self, view):
        """Bind to the GameView; pull out the widgets you need to mutate."""
        self.rules = view.rules

    def tick(self, frame_factor):
        """Advance by one frame; frame_factor = dt * 60."""
        ...


def _make_speed(view):
    """Create the speed effect bound to the given GameView."""
    return SpeedEffect(view)


EFFECT_FACTORIES: dict[str, Callable] = {
    "potion_magnetism": _make_magnet,
    "potion_speed": _make_speed,
}
```

- Factory signature: `f(GameView) -> RunEffect`. The view exposes `hero`,
  `entities` (live widget lists per type, e.g. `view.entities["flower"]`),
  `rules` (the live `GameRules`), and `hud`.
- Effects mutate widget state per frame; keep them stateless where possible
  and derive from the view.
- A recipe whose id is missing from `EFFECT_FACTORIES` still loads, brews,
  and is consumed on use — it just has no effect (logged as a warning).
  If you ship a recipe without an effect deliberately, add a test pinning
  that behavior (see `test_potion_without_registered_effect_is_consumed_and_listed`).

## 4. Tests

- `tests/unit/test_potions.py` — the recipe must load (valid entry), and
  `match_recipe` finds it with exactly the right cauldron contents.
- `tests/unit/test_game_scene.py` — one test per effect: using a filled
  slot activates it, it ticks, it expires after `duration_seconds`, HUD
  label shows name + seconds. Patterns:
  `test_hotkey_uses_filled_slot_and_activates_effect`,
  `test_effect_expires_and_label_cleared`.
- No changes needed in `tests/unit/test_profiles.py` — the save format is
  id-keyed and generic.

Verify: `make test` and `make check-all`.

## Gotchas

- Cauldron UI shows at most 4 ingredient **types** (2x2 grid); recipes with
  5+ distinct ingredients are unbrewable in the UI.
- Only flowers dropped by levels exist in inventories — a recipe built from
  a sprite no level drops is dead content.
- `potion_id` in save data is the recipe `id`. Renaming an id orphans
  existing players' potions: the counts stay in `config.yaml`, still show in
  the UI with the raw untranslated key, and using them just logs a warning
  and wastes the potion. Old entries are never pruned.
