---
description: "Task list for Sprite Manager feature implementation"
---

# Tasks: Sprite Manager

**Input**: Design documents from `/specs/002-sprite-manager/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Add `pyyaml` dependency to the project using `uv add pyyaml`
- [x] T002 [P] Create `src/quick_herbalist/core/` directory structure with `__init__.py`
- [ ] T003 [P] Create `src/quick_herbalist/tools/sprite_editor/ui/` directory structure with `__init__.py`
- [ ] T004 [P] Register the `manage-sprites` CLI script entry point in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Write unit tests for pure configuration parsing functions in `tests/unit/test_config_parser.py`
- [ ] T006 Implement YAML and Atlas reading/writing functions in `src/quick_herbalist/core/config_parser.py`

**Checkpoint**: Foundation ready - config parser is tested and working. User story implementation can now begin.

---

## Phase 3: User Story 1 - Create and Edit Sprite Animations (Priority: P1) 🎯 MVP

**Goal**: Standalone GUI application to define and edit sprite animations using original source images without writing raw JSON/YAML manually.

**Independent Test**: Launch the CLI GUI app, add a new sprite, assign image files, set durations, save, and verify `assets/sprites.yaml` and `assets/sprites.atlas` are generated correctly.

### Implementation for User Story 1

- [ ] T007 [P] [US1] Create GUI application entry point in `src/quick_herbalist/tools/sprite_editor/__main__.py`
- [ ] T008 [P] [US1] Create basic Kivy App class in `src/quick_herbalist/tools/sprite_editor/app.py`
- [ ] T009 [US1] Implement sprite preview widget with zoom (+/-) in `src/quick_herbalist/tools/sprite_editor/ui/preview.py`
- [ ] T010 [US1] Implement frame sequence and duration editor in `src/quick_herbalist/tools/sprite_editor/ui/sequence_editor.py`
- [ ] T011 [US1] Implement main layout bringing preview and sequence editor together in `src/quick_herbalist/tools/sprite_editor/ui/main_layout.py`
- [ ] T012 [US1] Wire GUI save actions to `config_parser.py` to write `assets/sprites.yaml` and `assets/sprites.atlas`

**Checkpoint**: At this point, User Story 1 should be fully functional. Developers can create/edit sprites via GUI.

---

## Phase 4: User Story 2 - Render Sprites in Game (Priority: P1)

**Goal**: Request a sprite by name from the SpriteManager and receive a fully functional UI widget autonomously animating.

**Independent Test**: Run a test Kivy app that instantiates SpriteManager, requests 'hero_run', and displays it animating.

### Tests for User Story 2

- [ ] T013 [P] [US2] Write unit tests for SpriteManager and AnimatedSprite widget in `tests/unit/test_sprite_manager.py`

### Implementation for User Story 2

- [ ] T014 [US2] Implement custom autonomous Kivy widget `AnimatedSprite` in `src/quick_herbalist/core/animated_sprite.py`
- [ ] T015 [US2] Implement `SpriteManager` class to load configs and return widgets in `src/quick_herbalist/core/sprite_manager.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. The game can render what the GUI creates.

---

## Phase 5: User Story 3 - Validate Configurations on GUI Startup (Priority: P2)

**Goal**: GUI application automatically cross-checks YAML and Atlas files upon startup, alerting to orphaned data.

**Independent Test**: Launch GUI with artificially corrupted `sprites.yaml` and observe the warning dialog.

### Tests for User Story 3

- [ ] T016 [P] [US3] Add validation logic tests to `tests/unit/test_config_parser.py`

### Implementation for User Story 3

- [ ] T017 [US3] Add configuration integrity validation function to `src/quick_herbalist/core/config_parser.py`
- [ ] T018 [US3] Implement warning popup dialogue in `src/quick_herbalist/tools/sprite_editor/app.py` triggered on startup failure

**Checkpoint**: All user stories should now be independently functional. Configurations are strictly validated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T019 [P] Execute Scenario 1 and 2 from `specs/002-sprite-manager/quickstart.md` manually to verify end-to-end integration
- [ ] T020 Review type hints and PEP8 formatting using `pre-commit run --all-files`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 and User Story 2 can proceed in parallel.
  - User Story 3 depends on User Story 1 (GUI base).
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2). Strictly depends on the config parser, but independent of the GUI.
- **User Story 3 (P2)**: Extends User Story 1 and the config parser.

### Parallel Opportunities

- T002, T003, T004 in Setup can run in parallel.
- US1 (GUI) and US2 (Game Runtime) can be developed in parallel by different developers once `config_parser.py` is implemented.
- Unit tests can be written in parallel before their corresponding implementations.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently using the GUI.

### Incremental Delivery

1. Complete Setup + Foundational.
2. Add User Story 1 (GUI) → Validate.
3. Add User Story 2 (Runtime) → Validate using quickstart scenario 2.
4. Add User Story 3 (Validation) → Validate using corrupted YAML.