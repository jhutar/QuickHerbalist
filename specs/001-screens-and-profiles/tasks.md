# Tasks: Screen Refactor & Character Profiles

**Input**: Design documents from `specs/001-screens-and-profiles/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests are defined to align with Principle III and IV of the Constitution, running fully headlessly without spawning a Kivy application instance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- exact file paths are included in task descriptions

## Path Conventions
- Standard single project layout: Source code under `src/quick_herbalist/`, unit tests under `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project dependency and basic testing layout initialization

- [X] T001 Add `pyyaml` dependency to `pyproject.toml`
- [X] T002 [P] Create basic unit test structure under `tests/unit/test_profiles.py` with pytest configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure-Python decoupled storage and manager class initialization

**⚠️ CRITICAL**: No user story GUI development can begin until this data core is ready and verified

- [X] T003 Implement `ProfileManager` and config file folder resolution in `src/quick_herbalist/profiles.py`
- [X] T004 [P] Implement YAML configuration loading, saving, and defaults recovery in `src/quick_herbalist/profiles.py`
- [X] T005 Write unit tests for configuration loading, saving, fallback, and corruption recovery in `tests/unit/test_profiles.py`

**Checkpoint**: Foundation ready - decoupled storage state machine can now be used by user story screens

---

## Phase 3: User Story 1 - Profile Creation and Selection (Priority: P1) 🎯 MVP

**Goal**: Create, select, save, and load multiple character profiles from standard screens.

**Independent Test**: Launch application, select "New Character", enter name, confirm, see it displayed as active on Menu screen, and verify written `config.yaml` exists in user data folder.

### Tests for User Story 1

- [X] T006 [P] [US1] Write unit tests for character creation validations (duplicate, empty, or whitespace name rejections) in `tests/unit/test_profiles.py`
- [X] T007 [P] [US1] Write unit tests for character loading and switching in `tests/unit/test_profiles.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement `create_character` and `select_character` methods with validations in `src/quick_herbalist/profiles.py`
- [X] T009 [US1] Instantiate global `ProfileManager` instance and integrate it during application builder startup in `src/quick_herbalist/game.py`
- [X] T010 [US1] Implement Kivy `NewCharacterScreen` layout, validation input fields, error warnings, and confirmation buttons in `src/quick_herbalist/game.py`
- [X] T011 [US1] Implement Kivy `LoadCharacterScreen` dynamically listing created characters and switching profile on select in `src/quick_herbalist/game.py`
- [X] T012 [US1] Update `MenuScreen` layout in `src/quick_herbalist/game.py` to display active character name and bind 'n' and 'l' keys for screen navigation
- [X] T013 [US1] Update startup logic in `src/quick_herbalist/game.py` to skip the main menu and redirect directly to `NewCharacterScreen` if active character is None

**Checkpoint**: User Story 1 is fully functional as a standalone MVP profile creation/switching system

---

## Phase 4: User Story 2 - Game Flow & Win Condition (Priority: P2)

**Goal**: Track distance, reach target level distance, transition to "Game Won" screen, and reward collected flowers.

**Independent Test**: Play game with active profile, reach 1000m target, see "Level Completed!" screen, and verify flowers added to profile YAML inventory count.

### Tests for User Story 2

- [ ] T014 [P] [US2] Write unit tests for profile reward additions (`add_rewards` state changes) in `tests/unit/test_profiles.py`

### Implementation for User Story 2

- [ ] T015 [US2] Implement `add_rewards` method in `src/quick_herbalist/profiles.py`
- [ ] T016 [US2] Create Kivy `GameWonScreen` showing completion state, buttons to play again or return to menu, and bind 'escape'/'q' in `src/quick_herbalist/game.py`
- [ ] T017 [US2] Update `GameView` widget in `src/quick_herbalist/game.py` to show active character name in the top corner of the HUD
- [ ] T018 [US2] Update `GameView.update` loop in `src/quick_herbalist/game.py` to verify distance against `win_distance` from global settings, stop game runs, invoke `add_rewards`, and transition to `GameWonScreen` on success

**Checkpoint**: Gameplay loop transitions to victory screen and records inventory updates in profiles

---

## Phase 5: User Story 3 - Potions Screen and Navigation (Priority: P3)

**Goal**: Access placeholder Create Potions screen and return back to main menu.

**Independent Test**: Press 'c' on Main Menu to transition to Create Potions screen, click "Back to Menu" to return.

### Implementation for User Story 3

- [ ] T019 [US3] Create Kivy `PotionsScreen` placeholder layout and back button in `src/quick_herbalist/game.py`
- [ ] T020 [US3] Update `MenuScreen` key bindings in `src/quick_herbalist/game.py` to map 'c' shortcut to switch to `PotionsScreen`

**Checkpoint**: Core screens navigation complete and user stories are fully connected

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Code cleanup, formatting, localization, and manual validations

- [ ] T021 [P] Wrap all newly added UI text strings with Gettext `_()` translations in `src/quick_herbalist/game.py`
- [ ] T022 [P] Verify code style, formatting, and linting standards using pre-commit on command line
- [ ] T023 Run E2E validation scenarios defined in `specs/001-screens-and-profiles/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies - starts immediately.
- **Foundational (Phase 2)**: Depends on T001/T002 - BLOCKS all screens work.
- **User Story 1 (Phase 3)**: Depends on Phase 2. First complete screens flow.
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs active profiles).
- **User Story 3 (Phase 5)**: Depends on Phase 3 (needs menu screen base).
- **Polish (Phase 6)**: Depends on Phase 3, 4, 5.

### Parallel Opportunities
- T002 (Setup test structure) can be worked on concurrently with T001.
- T004 (YAML save/load methods) can be created in parallel with T003.
- All test tasks (T006, T007, T014) can be developed in parallel prior to GUI implementation.
- Story 2 (T017 HUD name) and Story 3 (T019 Potions Screen) can run in parallel by different developers once active profile menu is complete.
- Polish tasks (T021, T022) are highly parallelizable.

---

## Parallel Example: User Story 1

```bash
# Developer A writes backend/core tests headlessly:
Task: "Write character creation validation tests in tests/unit/test_profiles.py"
Task: "Write character selection tests in tests/unit/test_profiles.py"

# Developer B implements backend logic:
Task: "Implement create_character and select_character in src/quick_herbalist/profiles.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Setup project dependencies (`pyyaml`).
2. Implement and test headless `ProfileManager` storage.
3. Build user story 1 Kivy screens (`NewCharacterScreen`, `LoadCharacterScreen`, update `MenuScreen`).
4. Validate that you can create, persistent-save, and reload players on start.

### Incremental Delivery
- **Increment 1 (MVP)**: Full character profile creation, saving, and switching (US1).
- **Increment 2**: Game win condition triggers inventory updates for the active character (US2).
- **Increment 3**: Access to all navigation links (US3).
- **Increment 4**: Complete translation wrapping and lint formatting.
