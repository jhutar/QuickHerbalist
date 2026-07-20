# Implementation Plan: Sprite Manager

**Branch**: `[002-sprite-manager]` | **Date**: 2026-07-19 | **Spec**: [specs/002-sprite-manager/spec.md](spec.md)

**Input**: Feature specification from `/specs/002-sprite-manager/spec.md`

## Summary

Build a two-part Sprite Management system:
1. `SpriteManager`: A game runtime class that loads relational skinny YAML and standard Kivy `.atlas` JSON files to return fully functional, autonomously animating Kivy UI widgets.
2. **Standalone GUI**: A developer CLI application that abstracts the `.atlas` complexity, allowing users to visually create and edit sprites and frame-level durations using non-destructive references to source images in the `assets/` directory.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Kivy (>= 2.3.0), PyYAML (for reading/writing YAML config)

**Storage**: Local files (`assets/sprites.yaml`, `assets/sprites.atlas`)

**Testing**: pytest

**Target Platform**: Desktop (for the GUI editor), Multi-platform (PC/Mobile) for the game runtime.

**Project Type**: Game Engine Component & Developer GUI Tool

**Performance Goals**: Negligible initialization overhead. The game must load the atlas and yaml rapidly.

**Constraints**:
- The standalone GUI MUST be isolated from the game runtime.
- The `SpriteManager` MUST decouple configuration loading from rendering to support unit testing.
- Must use `get_asset_path` for loading resources.

**Scale/Scope**: Dozens to hundreds of sprites; small to medium sized image files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Multi-Platform Delivery**: The core `SpriteManager` uses standard Kivy features which are cross-platform. The GUI tool is desktop-focused but built on Kivy.
- [x] **II. Pragmatic Architecture**: `SpriteManager` will be an OOP class. YAML parsing and ID validation can be functional and pure.
- [x] **III. Maintainability & Testability**: `SpriteManager` logic for reading and matching YAML to Atlas IDs must be completely decoupled from actual Kivy Image instantiation to allow unit testing without a GUI environment.
- [x] **IV. Automated Testing Discipline**: Unit tests will cover YAML parsing, ID resolution, and error handling for missing files/IDs.
- [x] **V. Localization and Resource Management**: `SpriteManager` and the GUI will use `get_asset_path` for locating the `sprites.yaml` and `sprites.atlas` files.

## Project Structure

### Documentation (this feature)

```text
specs/002-sprite-manager/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── yaml-schema.md
│   └── atlas-schema.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/quick_herbalist/
├── core/
│   ├── sprite_manager.py     # Main runtime abstraction
│   └── config_parser.py      # Pure functions for reading/writing YAML and Atlas
├── tools/
│   └── sprite_editor/        # Standalone GUI tool
│       ├── __main__.py       # CLI Entry point
│       ├── app.py            # Kivy App definition
│       └── ui/               # Editor widgets and layouts
└── assets/
    ├── sprites.yaml
    └── sprites.atlas

tests/
├── unit/
│   ├── test_sprite_manager.py
│   └── test_config_parser.py
```

**Structure Decision**: The logic is split into the runtime `core/` (used by the game) and developer-only `tools/` (the standalone editor). Pure configuration manipulation is separated into `config_parser.py` to maximize testability per Constitution Principle III.
