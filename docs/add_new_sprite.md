# Adding a new sprite

Sprites are defined in two files, both in `src/quick_herbalist/assets/`:

- `sprites.atlas` — maps image files to named regions. Each region is a JSON
  4-tuple `[x, y, w, h]` in pixels. Keys are the image filename (no directory,
  no extension path).
- `sprites.yaml` — maps sprite names to an ordered list of frames. Each frame
  references an `atlas_id` and has a `duration_ms` (playback time in
  milliseconds).

A sprite with one frame is a still image; several frames with equal
`duration_ms` give a uniform animation.

## Steps

1. Put the image file(s) in `src/quick_herbalist/assets/`.
2. Add an atlas region for each frame in `sprites.atlas`. If the image is used
   whole, the region is `[0, 0, width, height]`:

   ```json
   "flower2.png": {
     "flower2_sprite_0": [0, 0, 64, 64]
   }
   ```
3. Add the sprite in `sprites.yaml`:

   ```yaml
   flower2_sprite:
     frames:
     - atlas_id: flower2_sprite_0
       duration_ms: 250
   ```

Use the `<name>_sprite_<index>` convention for `atlas_id`s, matching the
sprite name, so the atlas is self-explanatory.

Either edit the two files by hand or use the sprite editor GUI
(`python -m quick_herbalist.tools.sprite_editor`), which writes both files and
validates consistency on save.

## Verify

`SpriteConfig.validate(sprites.yaml, sprites.atlas)` must return `True`
(mismatches show as a popup in the sprite editor), and every `atlas_id`
referenced in `sprites.yaml` must exist in `sprites.atlas`. The game resolves
sprites through `SpriteManager.get(name)`; an unknown name raises
`ValueError` at load time.

## Flower sprites: human-readable name

A sprite used as a level flower (the `flower.sprite` key in `levels.yaml`) is
also a collectable inventory type, keyed by its sprite name, and the only
source of potion brewing ingredients (`docs/add_new_potion.md`). Add a
display name for it in the translation files: one `msgid "<sprite_name>"` entry with
the human name as `msgstr` in
`src/quick_herbalist/locales/en/LC_MESSAGES/base.po` and the Czech translation
in `.../cs/LC_MESSAGES/base.po` (plus the empty entry in `locales/base.pot`),
then recompile with `python scripts/compile_mo.py` on the changed `.po`
files. Without a translation the raw sprite name is shown in the win screen
harvest list.
