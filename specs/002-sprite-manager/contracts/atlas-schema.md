# Contract: sprites.atlas

**Format**: JSON

This is a standard Kivy Atlas file. It maps unique string IDs to texture regions within source images.

## Schema

```json
{
  "<source_image_filename>": {
    "<atlas_id>": [<x>, <y>, <width>, <height>],
    // ... more regions ...
  },
  // ... more source images ...
}
```

## Constraints
- The `<source_image_filename>` must be a valid path relative to the directory containing the `.atlas` file (e.g., `hero.png`, assuming both are in the `assets/` folder).
- Coordinates `[x, y]` define the **bottom-left** corner of the region, which is standard for Kivy.

## Example

```json
{
  "hero.png": {
    "hero_run_0": [0, 0, 32, 32],
    "hero_run_1": [32, 0, 32, 32]
  },
  "environment.png": {
    "flower_static_0": [0, 64, 16, 16]
  }
}
```
