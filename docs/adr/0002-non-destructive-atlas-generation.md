# Architecture Decision Record

## Title
Non-Destructive Atlas Generation

## Status
Accepted

## Context
The GUI tool needs to manage texture regions (via Kivy Atlas) to define Sprite Frames. We need to decide how the tool handles the source image files (e.g., `hero_walk.png`) provided by the user. Kivy's default Atlas behaviour is to pack multiple small images into a single large master image.

## Decision
We will use a **Non-Destructive/Referential** approach. The GUI will not repack source images into a new master sprite sheet. Instead, the user will place their source images directly into the `assets/` folder, and the GUI will generate an `.atlas` JSON file that maps regions directly onto those existing, original asset files.

## Consequences
- **Positive:** Users retain control over their original files. They can edit `hero_walk.png` externally and the regions will still apply (as long as the layout doesn't change).
- **Positive:** Fits the requested workflow where a user selects a specific file and defines an `(x, y, w, h)` region within it.
- **Negative:** We miss out on the theoretical performance benefits of packing many small textures into a single large texture, though this is likely negligible for a "quick 2D items-collecting game".