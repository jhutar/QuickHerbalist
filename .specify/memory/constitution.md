<!--
### Sync Impact Report
- Version change: None -> 1.0.0
- Modified principles:
  * [PRINCIPLE_1_NAME] -> I. Multi-Platform Delivery (PC & Mobile)
  * [PRINCIPLE_2_NAME] -> II. Pragmatic Multi-Paradigm Architecture
  * [PRINCIPLE_3_NAME] -> III. Maintainability and High Testability (NON-NEGOTIABLE)
  * [PRINCIPLE_4_NAME] -> IV. Automated Testing Discipline
  * [PRINCIPLE_5_NAME] -> V. Localization and Resource Management
- Added sections:
  * Technology Stack Constraints
  * Development and Quality Workflow
- Removed sections: None
- Templates requiring updates:
  * .specify/templates/plan-template.md (✅ no changes required)
  * .specify/templates/spec-template.md (✅ no changes required)
  * .specify/templates/tasks-template.md (✅ no changes required)
- Follow-up TODOs: None
-->

# QuickHerbalist Constitution

## Core Principles

### I. Multi-Platform Delivery (PC & Mobile)
The game MUST support both PC and mobile deployment targets. The codebase MUST utilize Kivy as the unifying cross-platform UI framework. Platform-specific code MUST be strictly isolated behind clean abstractions or dynamic adapters, ensuring that the core game state and logic remain completely platform-independent.

### II. Pragmatic Multi-Paradigm Architecture
The codebase MUST pragmatically combine Object-Oriented Programming (OOP) and functional-based programming. OOP MUST be used where stateful UI components, screens, and game entities benefit from encapsulation and inheritance. Pure functional programming or stateless logic MUST be preferred for mathematical calculations, data transformations, and state-free utilities to maximize predictability and reuse.

### III. Maintainability and High Testability (NON-NEGOTIABLE)
All logic MUST be written with high testability and maintainability in mind. Complex state transitions, game loop updates, and localization functions MUST be decoupled from Kivy's UI rendering layer so they can be unit-tested in isolation without starting a GUI environment. Clean, modular code structure is mandatory.

### IV. Automated Testing Discipline
Since the test suite is newly established, any new feature or bug fix MUST include automated tests. We MUST support standard unit tests using Python's standard `unittest` or `pytest`. Test execution MUST be simple and standard.

### V. Localization and Resource Management
The game MUST support localization (Gettext-based) and clean asset management. All assets and locale files MUST be loaded via structured path utilities (`get_asset_path`, `get_locales_dir`). Hardcoded asset paths or unlocalized user-facing strings are strictly forbidden.

## Technology Stack Constraints

- **Language**: Python 3.11+
- **Framework**: Kivy (>= 2.3.0) for UI, multi-platform deployment.
- **Dependency Management**: Managed exclusively with `uv` (using `pyproject.toml` and `uv.lock`).
- **Linter & Formatter**: pre-commit with Ruff (as defined in `.pre-commit-config.yaml`).

## Development and Quality Workflow

- **Formatting & Style**: All Python code MUST strictly adhere to PEP 8 standards and Ruff linting rules. Running `pre-commit run --all-files` is required before committing any change.
- **UI and Logic Separation**: Developers MUST separate Kivy Kv design files (if used) or UI layout definitions from logical state management.

## Governance

Amendments to this Constitution require updating `.specify/memory/constitution.md`, incrementing the version, and documenting the changes in the Sync Impact Report at the top of the file. All code changes and pull requests MUST be verified against these principles. Use `GEMINI.md` as the primary runtime developer guidance file for specific technical tasks and workspace workflows.

**Version**: 1.0.0 | **Ratified**: 2026-07-18 | **Last Amended**: 2026-07-18
