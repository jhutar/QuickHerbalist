# Feature Specification: Screen Refactor & Character Profiles

**Feature Branch**: `001-screens-and-profiles`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Load @/home/jhutar/.gemini/tmp/quickherbalist/ba663df1-e2b7-40ba-9873-6acb1126f9ce/plans/screens_and_profiles.md as a specification"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Profile Creation and Selection (Priority: P1)

As a player, I want to create and select a character profile, so that my game progress is personal and saved across game sessions.

**Why this priority**: Core foundational feature to enable persistent state, multiple players, and progress saving.

**Independent Test** (user performed): Start the app, go to "New Character", enter name, confirm, see that name on the Menu screen, and check that a YAML file is generated in the user data directory containing this name.

**Acceptance Scenarios**:

1. **Given** the app is started for the first time, **When** the Menu screen is displayed, **Then** the current character displays as empty or None.
2. **Given** the Menu screen, **When** the user selects "New Character" (or presses 'n'), enters name "HerbalistMax" and confirms, **Then** the app switches to the Menu screen, displays "HerbalistMax" as current character, and saves the character to the configuration file.
3. **Given** multiple characters exist, **When** the user selects "Load Character" (or presses 'l'), selects "HerbalistMax" from the list, **Then** the app sets "HerbalistMax" as current and switches to the Menu screen.
4. **Given** the app is started, **When** no character is selected, **Then** skip main menu and go directly to "New Character" menu

---

### User Story 2 - Game Flow & Win Condition (Priority: P2)

As a player, I want to play the game and complete a level by reaching the win distance, so that my character can win and store rewards in their inventory.

**Why this priority**: Core gameplay loop completion to provide player engagement and test the game loop state transitions.

**Independent Test** (user performed): Start the game with an active character, play until target distance is reached, verify transition to the Game Won screen, and check that the inventory is updated.

**Acceptance Scenarios**:

1. **Given** an active character is loaded, **When** the game is started, **Then** the game screen displays the character's name in the corner and starts tracking distance.
2. **Given** the game is running, **When** the player reaches the win distance, **Then** the game transitions to the "Game Won" screen, shows "Level Completed!", and awards collected flowers to the character's inventory in the configuration file.

---

### User Story 3 - Potions Screen and Navigation (Priority: P3)

As a player, I want to navigate to the Create Potions screen and other options screens, so that I have access to game features and can easily quit/resume.

**Why this priority**: Enhances the user flow and provides placeholder support for future features without blocking core functionality.

**Independent Test** (user performed): Press 'c' on the Menu, verify transition to the Create Potions placeholder screen, and press back to return to the Menu.

**Acceptance Scenarios**:

1. **Given** the Menu screen, **When** the user presses 'c' or clicks "Create Potions", **Then** the app transitions to the Create Potions screen.
2. **Given** the Create Potions screen, **When** the user clicks "Back to Menu", **Then** the app transitions back to the Menu screen.

---

### Edge Cases

- **Empty or Whitespace-Only Name**: System MUST prevent creation of a character with an empty, whitespace-only, or invalid name, showing an appropriate error or disabling the confirm button.
- **Duplicate Names**: System MUST prevent creation of a character with a name that already exists in the profile configuration file.
- **Missing or Corrupted Save File**: If the configuration file is missing or corrupted, the system MUST automatically regenerate a default structure without crashing.
- **Unsaved Progress**: If the user exits the game abruptly (e.g., closing the window), the current game run distance is lost, but the persistent profile inventory remains unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a cross-platform multi-screen flow using Kivy Screens (Menu, New Character, Load Character, Create Potions, Game, Game Won, Game Over, Quit).
- **FR-002**: System MUST persist character profiles (name, levels_completed, inventory) in a YAML configuration file (`config.yaml`) within the OS-appropriate user data directory (consider this will run on mobile as well, e.g. Android).
- **FR-003**: System MUST update the active character's inventory (e.g., flowers collected) and levels completed upon successful completion of a level.
- **FR-004**: System MUST support keyboard shortcuts on appropriate screens ('n' for new, 'l' for load, 's' for start, 'c' for potions, 'q' for quit).
- **FR-005**: System MUST trigger the "Game Won" screen when the player reaches the target `win_distance`.
- **FR-006**: System MUST show the active character's name clearly on the Menu screen and on the Game screen.

### Key Entities *(include if feature involves data)*

- **ProfileManager**: Singleton/global state manager that coordinates saving, loading, creating, and switching active characters.
- **Character**: Represented in YAML with a unique name, `levels_completed` integer, and `inventory` dictionary (containing a `flower` count).
- **Settings**: Global configuration containing `fps` integer, `win_distance` float, and `game_speed_start` float.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Players can create a new character, start a game, win, and see their profile inventory updated in the YAML file in under 3 minutes.
- **SC-002**: Transition between screens (Menu, Game, Game Won, etc.) occurs instantly with zero visible stutter or lag.
- **SC-003**: Profile save file writes successfully and safely, surviving application restarts.
- **SC-004**: The save file path is resolved dynamically using standard OS conventions (Windows, Linux, macOS).

## Assumptions

- **AS-001**: Kivy's `App.get_running_app().user_data_dir` provides a valid and writable path on all target operating systems.
- **AS-002**: PyYAML is available and can be added as a project dependency in `pyproject.toml`.
- **AS-003**: Kivy is the sole UI and game engine framework as defined in the constitution.
