# Implementation Plan: Screen Refactor & Character Profiles

**Branch**: `001-screens-and-profiles` | **Date**: 2026-07-18 | **Spec**: `specs/001-screens-and-profiles/spec.md`

**Input**: Feature specification from `specs/001-screens-and-profiles/spec.md`

## Summary
Refactor the single-screen game structure into a robust, cross-platform multi-screen flow using Kivy's `ScreenManager`. Implement a persistent profile management system that saves player names, levels completed, and inventory rewards into a `config.yaml` file located in the OS-appropriate user data directory. The profile logic is fully decoupled from the UI rendering layer, making it highly testable and robust.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Kivy (>= 2.3.0), PyYAML (>= 6.0)

**Storage**: YAML file (`config.yaml`) in OS-appropriate user data directory (`App.get_running_app().user_data_dir`)

**Testing**: pytest (runs headlessly, decoupled from Kivy)

**Target Platform**: Linux, Android, Windows, macOS (Multi-Platform Mobile & Desktop)

**Project Type**: desktop-app / mobile-app

**Performance Goals**: 60 FPS rendering, instant (stutter-free) screen transitions

**Constraints**: <100MB memory footprint, offline-capable save files, game loop completely decoupled from graphics for isolated test coverage.

**Scale/Scope**: 8 total Screens (`menu`, `new_character`, `load_character`, `options`, `game`, `game_won`, `game_over`, `quit`), single `config.yaml` with arbitrary number of characters.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Multi-Platform Delivery**: Verified. Uses cross-platform Kivy ScreenManager and `App.get_running_app().user_data_dir` to work seamlessly on PC and Android.
- **II. Pragmatic Multi-Paradigm Architecture**: Verified. State and serialization are managed by a pure-Python OOP `ProfileManager`. Screen transitions and UI widgets inherit from Kivy OOP classes.
- **III. Maintainability and High Testability (NON-NEGOTIABLE)**: Verified. All profile management logic is entirely decoupled from the Kivy application lifecycle, enabling full headless unit testing.
- **IV. Automated Testing Discipline**: Verified. Tests under `tests/` will run in standard CI/CD without requiring X11/GUI framebuffers.
- **V. Localization and Resource Management**: Verified. Newly introduced labels are wrapped in standard Gettext `_()` translations.

## Project Structure

### Documentation (this feature)

```text
specs/001-screens-and-profiles/
├── plan.md              # This file
├── research.md          # Decision log and architectural rationale
├── data-model.md        # Persistent schemas and entity descriptions
├── quickstart.md        # Guide on how to run tests and manual E2E checks
└── contracts/
    └── profile-api.md   # Programmatic and UI transition contracts
```

### Source Code

```text
src/
└── quick_herbalist/
    ├── __init__.py
    ├── __main__.py
    ├── game.py          # Unified game app and screen navigation
    ├── profiles.py      # Decoupled ProfileManager and serialization logic
    └── locales/         # Translation dictionaries
tests/
└── unit/
    └── test_profiles.py # Headless unit tests for profiles and config
```

**Structure Decision**: Selected a Single Project structure as the repository is cohesive and self-contained. `profiles.py` is isolated to encapsulate pure game data logic separate from GUI elements.

## Complexity Tracking

> *No violations to justify. Architecture perfectly aligns with Constitution.*
