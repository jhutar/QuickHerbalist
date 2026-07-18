# Data Model: Screen Refactor & Character Profiles

This document specifies the logical data models, validation rules, and configuration file format for the Screens and Profiles feature.

## Configuration File Schema

All character profiles and global settings are persisted in `config.yaml` located in the OS-appropriate user data directory.

```yaml
# config.yaml structure
active_character: "HerbalistMax" # Name of current selected character, or null/empty

settings:
  fps: 60
  win_distance: 1000.0
  game_speed_start: 3.0

characters:
  HerbalistMax:
    name: "HerbalistMax"
    levels_completed: 2
    inventory:
      flower: 15
  AnotherHero:
    name: "AnotherHero"
    levels_completed: 0
    inventory:
      flower: 0
```

---

## Key Entities

### 1. Character
Represents a player profile.
- **Fields**:
  - `name` (string, unique): Case-sensitive identifier of the character.
  - `levels_completed` (integer, default: 0): Total levels won by this character.
  - `inventory` (dictionary): Key-value collection of collected items. Must support `flower` count integer (default: 0).

- **Validation Rules**:
  - **No Empty/Whitespace Names**: The character name must be non-empty and contain at least one non-whitespace character after stripping.
  - **Uniqueness**: The character name must be unique within the save configuration. Cannot overwrite an existing character unless explicitly specified.
  - **Integrity**: Missing fields on loaded characters (e.g., loaded from a manually modified YAML file) must fall back to their defaults safely.

---

### 2. Settings
Global configuration options.
- **Fields**:
  - `fps` (integer, default: 60): Target frames per second.
  - `win_distance` (float, default: 1000.0): Distance required to win a level.
  - `game_speed_start` (float, default: 3.0): Starting horizontal speed of the player's run.

---

### 3. ProfileManager
A logic class that encapsulates all character persistence and selection state.
- **State**:
  - `active_character_name` (string or None): The name of the selected character.
  - `characters` (dict mapping name to Character dictionary/object): Instantiated profiles.
  - `settings` (Settings object/dict): Global game settings.
- **Core Operations**:
  - `load_config()`: Decodes the YAML file. If file missing/corrupted, regenerates a safe default.
  - `save_config()`: Encodes and writes state to the YAML file safely.
  - `create_character(name)`: Validates name, creates a default Character instance, and writes to config.
  - `select_character(name)`: Sets the specified character as the active character.
  - `add_rewards(flower_count)`: Adds collected flowers to the active character's inventory and increments completed levels by 1.
