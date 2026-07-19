# Feature Specification: Sprite Manager

**Feature Branch**: `[002-sprite-manager]`

**Created**: 2026-07-19

**Status**: Draft

**Input**: User description: "I want to build new feature: It will have 2 parts: 1) Class in main game that loads config file and images (sprites) and provides it to the rest of the application 2) GUI application used to view, define, edit and delete existing sprites in the config file ..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Edit Sprite Animations (Priority: P1)

As a game developer, I want to use a standalone GUI application to define and edit sprite animations using my original source images, so that I can easily configure frame sequences and durations without writing raw JSON/YAML manually.

**Why this priority**: Without the ability to define sprites, the game engine has no configurations to load.

**Independent Test**: Can be fully tested by launching the CLI GUI app, adding a new sprite, assigning image files to its frames, setting durations, and verifying that the correct `sprites.yaml` and `sprites.atlas` files are generated.

**Acceptance Scenarios**:

1. **Given** the GUI application is open, **When** I create a new sprite and add frames referencing an image file (`assets/hero.png`), **Then** I can see the visual representation of the frames and adjust their position (`x, y, w, h`) and duration.
2. **Given** I have edited a sprite, **When** I save my changes, **Then** the application updates `assets/sprites.yaml` with sequence data and `assets/sprites.atlas` with static texture region mapping, without duplicating the source image.
3. **Given** the preview is open, **When** I click the zoom buttons (+/-), **Then** the preview scales appropriately (25%, 50%, 100%, 200%, 400%).
4. **Given** I have a frame selected, **When** I add a new frame, **Then** the new frame defaults to the same image and its `x` coordinate is advanced by its `width`.

---

### User Story 2 - Render Sprites in Game (Priority: P1)

As a game programmer, I want to request a sprite by name from the SpriteManager and receive a fully functional UI widget, so that I don't have to manually manage texture regions and animation clocks in my game entities.

**Why this priority**: The game needs to display the sprites created by the GUI tool.

**Independent Test**: Can be fully tested by instantiating the SpriteManager in a simple test app, requesting a known animated sprite, and observing the returned widget autonomously animating on screen.

**Acceptance Scenarios**:

1. **Given** valid `sprites.yaml` and `sprites.atlas` configurations exist in the `assets/` directory, **When** the game initializes the SpriteManager, **Then** it successfully parses the relational skinny YAML and the Atlas JSON.
2. **Given** the SpriteManager is initialized, **When** I call `SpriteManager.get('hero_run')`, **Then** it returns a widget that plays the 'hero_run' animation using the configured frame-level durations.

---

### User Story 3 - Validate Configurations on GUI Startup (Priority: P2)

As a game developer, I want the GUI application to automatically cross-check the YAML and Atlas files upon startup, so that I am alerted to any missing references or inconsistencies (e.g., an atlas_id in YAML that doesn't exist in the Atlas).

**Why this priority**: Ensures data integrity and prevents obscure runtime crashes in the game due to corrupted configurations.

**Independent Test**: Can be tested by manually removing an entry from `sprites.atlas` and launching the GUI to verify a warning is displayed.

**Acceptance Scenarios**:

1. **Given** an inconsistent configuration state (e.g. YAML refers to missing atlas ID), **When** I start the Sprite Manager GUI, **Then** the system detects the discrepancy and alerts me to the orphaned data.

### Edge Cases

- What happens when a requested sprite name does not exist in the YAML configuration?
- How does the system handle missing source image files referenced by the `.atlas` file?
- How does the GUI handle multiple users/processes trying to edit the configuration files simultaneously?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a `SpriteManager` class in the main game that loads `assets/sprites.yaml` and `assets/sprites.atlas` by convention.
- **FR-002**: The `SpriteManager` MUST return a fully functional, autonomously animating UI widget when a sprite is requested by name.
- **FR-003**: The system MUST provide a standalone GUI application (launched via CLI) for managing sprites.
- **FR-004**: The GUI MUST use a "Skinny" relational YAML format that stores sequence and duration data, referencing `atlas_id`s.
- **FR-005**: The GUI MUST manage texture regions non-destructively, pointing to original image files in the `assets/` directory using standard Atlas JSON format.
- **FR-006**: The GUI MUST allow configuration of frame-level durations for animations.
- **FR-007**: The GUI MUST cross-check the YAML and `.atlas` files on startup for consistency.
- **FR-008**: The GUI MUST hide the `.atlas` complexity from the user, presenting a unified "Sprite and Frame" editing experience.
- **FR-009**: The GUI MUST allow viewing an animated preview of the sprite with zoom controls (25%, 50%, 100%, 200%, 400%).
- **FR-010**: The GUI MUST auto-advance the `x` coordinate by `width` when adding a new frame to an existing sequence.

### Key Entities

- **Sprite**: A visual entity identifiable by name, consisting of one or more ordered Frames.
- **Frame**: A single step in an animation sequence, containing an `atlas_id` (linking to a texture region) and a `duration_ms`.
- **Texture Region**: Defines the source image file and the `(x, y, width, height)` boundaries of a graphic, stored in the Atlas JSON.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Game entities can retrieve and display an animated sprite with a single line of code.
- **SC-002**: Developers can create a new 5-frame animation from a sprite sheet using the GUI tool in under 1 minute.
- **SC-003**: All configuration states (YAML and Atlas) maintain 100% referential integrity after any GUI create, update, or delete operation.
- **SC-004**: The game application starts without developer-only GUI code loaded, ensuring a clean separation of concerns.

## Assumptions

- The game's assets folder is located at a fixed relative path (`assets/`) from the working directory.
- Developers have a local runtime environment configured for launching the standalone GUI application.
- Performance impact of not packing individual source images into a single master sheet is negligible for this project.
