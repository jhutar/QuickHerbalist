# Research & Decisions: Sprite Manager

**Status**: Complete

This document summarizes the technical decisions made during the architecture phase (via ADRs) to resolve the technical context for the Sprite Manager.

## Architectural Decisions

### 1. Kivy Atlas Abstraction
- **Decision**: Use Kivy's `Atlas` for static image regions, but abstract it behind a custom YAML configuration layer for animation sequences.
- **Rationale**: Kivy `Atlas` is highly optimized for texture management but lacks native support for animation sequences and frame durations. The GUI tool will hide the `.atlas` complexity from the developer.
- **Alternatives considered**: Building a purely custom texture packer/manager (discarded as reinventing the wheel and losing Kivy's native optimizations).

### 2. Non-Destructive Atlas Generation
- **Decision**: The GUI will map regions directly onto the user's original image files in `assets/` rather than packing them into a new master sprite sheet.
- **Rationale**: Retains user control over original files and fits the workflow of defining `(x, y, w, h)` regions on specific files.
- **Alternatives considered**: Destructive repacking (discarded as unnecessary for a small 2D game).

### 3. Standalone Sprite Manager GUI
- **Decision**: The GUI will be a standalone CLI entry point (e.g., `uv run manage-sprites`), completely separate from the game runtime.
- **Rationale**: Keeps the game codebase clean, prevents accidental production leaks of dev tools.
- **Alternatives considered**: In-game overlay triggered by a hotkey (discarded to avoid complex UI state conflicts).

### 4. Relational "Skinny" YAML Configuration
- **Decision**: The `sprites.yaml` will only store sequence orders and durations, referencing unique `atlas_id`s. The actual source paths and regions remain exclusively in the `sprites.atlas` JSON.
- **Rationale**: Prevents data duplication. Enforces a clear separation of concerns: YAML for sequence logic, Atlas for texture data.
- **Alternatives considered**: "Fat" YAML storing everything, with the Atlas treated purely as a build artifact (discarded to avoid data duplication and complex sync logic).

### 5. Convention over Configuration
- **Decision**: Both the game and GUI hardcode expectations for `assets/sprites.yaml` and `assets/sprites.atlas`.
- **Rationale**: Reduces boilerplate and ensures consistency.

## Required External Libraries
- `PyYAML`: Needed for parsing and dumping the `sprites.yaml` file. We must ensure this is added to the project dependencies (via `uv add pyyaml`). Kivy is already present.
