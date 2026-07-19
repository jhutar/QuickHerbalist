# Data Model: Sprite Manager

## Overview

The Sprite Manager relies on two interconnected configuration files to decouple texture data from animation logic.

## Entities

### Sprite
A requested visual entity in the game.
- **Fields**:
  - `name` (String, Primary Key)
  - `frames` (List of Frame objects)

### Frame
A single step in a sprite's animation sequence.
- **Fields**:
  - `atlas_id` (String): A reference to a texture region in the Atlas file.
  - `duration_ms` (Integer): Time in milliseconds this frame should be displayed (default: 250).

### TextureRegion
Defines a sub-rectangle within a physical source image file.
- **Fields**:
  - `id` (String, Primary Key): The `atlas_id` referenced by Frames.
  - `source_file` (String): The path to the physical image file relative to the `assets/` folder.
  - `x` (Integer): X coordinate of the bottom-left corner of the region.
  - `y` (Integer): Y coordinate of the bottom-left corner of the region.
  - `w` (Integer): Width of the region.
  - `h` (Integer): Height of the region.

## Relationships

- A **Sprite** contains one or more **Frames** (1-to-many).
- A **Frame** references exactly one **TextureRegion** via `atlas_id` (many-to-1).
- Multiple **Frames** (even across different **Sprites**) can reference the same **TextureRegion**.

## State Validation Rules
- Every `atlas_id` referenced in a Frame MUST exist as a TextureRegion in the Atlas.
- `duration_ms` MUST be > 0.
- `x`, `y`, `w`, `h` MUST be >= 0.