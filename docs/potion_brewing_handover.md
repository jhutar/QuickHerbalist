# Potion Brewing — Handover

Status of the potion brewing system after the brewing-screen work
(commits `33b054b`, `d4a1a70`, `faf6f02`). Read this to pick up where the
potion feature left off.

## What exists

### Brewing screen (`PotionsScreen`, screen name `potions`)

Accessible from the game menu hub (`GameMenuScreen`, "Create Potions" button or
`c` key). Layout top to bottom:

- **Ingredient inventory strip** — horizontal `ScrollView`, one draggable chip
  per flower type with count > 0 (image + localized name + `Nx`). Zero-count
  flowers hidden. Legacy/unknown sprite keys in the save are skipped with a
  warning, not crashed on.
- **Recipe book** — `<<<` / `>>>` flip through recipes, wrap-around. Shows
  name, description, ingredient list, duration over the `recipes.png`
  (128x128, stretched) background with a dark overlay; all text wraps to the
  panel size.
- **Cauldron** — `cauldron.png` with a 2x2 grid of ingredient slots. Same
  flower merges into one slot with a count badge in the lower right; tap a
  slot to return one unit to the inventory. Max 4 unique ingredients.
- **Spoon** — `star.png` placeholder, bottom-left of the cauldron. Drag the
  spoon onto the cauldron = mix/brew.
- **Run slots (3)** — bottom-left. Empty slots labelled `1` `2` `3`.
- **Potions inventory strip** — horizontal `ScrollView`, one chip per potion
  with count > 0 (`star.png` icon, localized name, `Nx`). Chips stack by type.
- **Message label** — brew results / errors (green success, red failure).

### Interaction rules

| Action | Result |
| --- | --- |
| Drag flower chip onto cauldron | 1 unit moves from profile inventory to cauldron (persisted immediately) |
| Drop flower outside cauldron | nothing happens |
| Tap ingredient slot in cauldron | 1 unit returns to profile inventory |
| Drag spoon onto cauldron | brew attempt |
| Brew, cauldron matches a recipe exactly | potion added to potions inventory, cauldron cleared, "Brewed: ..." |
| Brew, no match | **all cauldron ingredients permanently lost**, "Ingredients wasted" |
| Brew, empty cauldron | no-op |
| Click potion chip, or drag chip onto empty slot area | potion moved to first free run slot (costs 1 from potions inventory) |
| Drag potion chip onto a specific slot | placed in that slot if free, else first free |
| Click filled run slot | potion released back to potions inventory |

Recipe matching is an exact order-independent multiset equality: extra,
missing or over-counted ingredients all fail. The cauldron is never "reserved"
in the UI — units are physically moved, so leaving the screen mid-attempt is
safe (contents persist in the profile, including across restarts).

### Files

| File | Role |
| --- | --- |
| `src/quick_herbalist/potions.py` | Pure domain: `Recipe`, `load_recipes()` (fail-fast validation incl. unknown-ingredient check against `sprites.yaml`), `match_recipe()`, `RUN_SLOT_COUNT = 3` |
| `src/quick_herbalist/assets/recipes.yaml` | Recipe data. Currently one recipe: `potion_magnetism` = 2x `flower_sprite` + 1x `flower2_sprite`, 30 s |
| `src/quick_herbalist/profiles.py` | Persistence: `potions`, `run_loadout`, `cauldron` per character + methods `move_flower_to_cauldron`, `move_cauldron_ingredient_to_inventory`, `clear_cauldron`, `add_potion`, `consume_potion`, `assign_potion_to_slot`, `release_run_slot`, `get_*` accessors. Old saves auto-migrated in `_migrate_characters` |
| `src/quick_herbalist/screens.py` | `PotionsScreen` + KV, `Draggable` (hand-rolled drag&drop base, registered in Kivy `Factory`), `CauldronSlot` |
| `src/quick_herbalist/app.py` | Loads `recipes.yaml` at startup; invalid file = `SystemExit` (same pattern as levels) |
| `src/quick_herbalist/locales/` | en + cs strings for all brewing UI + `potion_magnetism_name` / `potion_magnetism_description` |
| `tests/unit/test_potions.py` | Recipe loading/validation/matching |
| `tests/unit/test_profiles.py` | Potion/loadout/cauldron persistence, migration, error codes |
| `tests/unit/test_screens.py` | Screen logic smoke tests (mocked Kivy) |

### Profile save shape (per character)

```yaml
name: herb
levels_completed: 2
inventory:            # flower sprite name -> count
  flower_sprite: 5
potions:              # potion id -> count
  potion_magnetism: 2
run_loadout:          # 3 entries, potion id or null
  - potion_magnetism
  - null
  - null
cauldron:             # sprite name -> count (unsaved-in-progress brew)
  flower_sprite: 1
```

New error codes in `ProfileErrorCode`: `INVALID_POTION_ID`,
`NOT_ENOUGH_POTIONS`, `NO_FREE_RUN_SLOT`, `INVALID_SLOT_INDEX`,
`RUN_SLOT_TAKEN`, `RUN_SLOT_EMPTY`, `NOT_ENOUGH_FLOWERS`, `NOT_IN_CAULDRON`.

### Adding a new recipe

1. Add `id: potion_x` entry to `assets/recipes.yaml` (ingredient keys must be
   sprite names from `sprites.yaml`; the app refuses to start otherwise).
2. Add `potion_x_name` / `potion_x_description` msgids to the locale `.po`
   files (and `base.pot`), compile `.mo` (pre-commit `compile-mo` hook does it
   when you stage `.po` files).
3. Potion icon is still the `star.png` placeholder everywhere.
4. Add tests where behavior changes.

### Drag&drop implementation notes

Kivy has no DnD widget in core (and `kivy_garden.draganddrop` is an external
dependency we avoid). It's ~60 lines in `Draggable`:

- `on_touch_down` on the widget starts a drag, spawns a proxy `Image` on the
  root window
- `on_touch_move` moves the proxy
- `on_touch_up` hit-tests `drop_target.collide_point`; a move > 15 px counts
  as drag, otherwise it's a click (`click_handler`)
- Custom widget classes used in KV **must** be registered in the `Factory`
  (`Factory.register("Draggable", cls=Draggable)`) — Kivy resolves KV class
  names through the Factory only. `Bar` scroll indicators were removed
  because Kivy 2 dropped the `Bar` widget.

### Tests

`make test` + `make check-all` (178 unit tests). Screen tests mock Kivy
modules; drag/touch paths are not unit-tested — only the commit handlers
(`_on_brew`, `_on_ingredient_dropped`, `_on_potion_dropped`, ...). Visual
behavior must be verified by hand: `uv run quick-herbalist`.

## What still needs to happen

In priority order as agreed with the player:

1. **In-run potion slots** — represent the 3 run slots in the game/run screen
   and bind using a potion to clicking the slot or pressing `1` / `2` / `3`.
   The loadout is already persisted; this is pure game-scene work.
2. **Potion consumption in-run** — using a potion removes it from
   `run_loadout`; a used potion is consumed even if the player dies afterwards
   (hits a stone). No in-run effect is implemented yet — `potion_magnetism`
   has no game effect (magnetize flowers within X px).
3. **Magnetism effect** — the actual gameplay: drag flowers up to X px toward
   the player for the recipe's duration. `duration_seconds` (30) is stored in
   `recipes.yaml` and shown in the book but **not enforced anywhere** — no
   timer, no active-effect system exists yet.
4. **Potion images** — replace `star.png` placeholders (potion chips, spoon)
   with real art via the sprite manager, like flowers.
5. **Recipes collected in-game** — players will collect recipes during runs
   later; currently all recipes in `recipes.yaml` are always available.
   Needs a per-profile "known recipes" set.
6. **Mixing gestures** — drag-spoon is the current "mix" gesture; richer
   per-recipe gestures were explicitly deferred.
7. **Legacy save data** — old profiles carry a generic `flower` inventory key
   that predates per-sprite tracking. It is skipped (with a warning) in the
   brewing screen but never migrated. If the old flower maps to
   `flower_sprite`, add a rename in `ProfileManager._migrate_characters`.
8. **More recipes/potions** — trivial data work once 1-3 exist (see
   "Adding a new recipe").

## Known rough edges

- Cauldron shows at most 4 **unique** ingredients (2x2 grid); a recipe could
  theoretically need more (validation does not cap it).
- No undo for a wasted brew by design ("Ingredients wasted" is permanent).
- Dragging from inside the horizontal `ScrollView` competes with scrolling
  (15 px threshold decides); felt-fine-or-not is untested on touch devices.
- Screen is laid out for the fixed 800x600 window; never resized/tested
  elsewhere.
- `PotionsScreen` state (recipe book page) lives on the screen instance and
  persists for the app session; everything else is profile-backed.
