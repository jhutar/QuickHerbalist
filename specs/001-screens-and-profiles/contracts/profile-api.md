# Profile API & CLI/UI Contracts

This contract documents the interface contracts exposed by `ProfileManager` to the rest of the application (UI, game screen, and test suite).

## 1. ProfileManager Interface API

The `ProfileManager` is instantiated as a class and coordinates save file operations.

### Method Signature: `__init__(self, config_dir: str = None)`
- **Parameters**:
  - `config_dir` (optional string): Explicit folder to save `config.yaml`. Used to inject temporary directory paths during unit testing to avoid polluting real user data directories. If `None`, dynamically resolves standard Kivy user_data_dir directory.

### Method Signature: `load_config(self) -> dict`
- **Behavior**: Reads and parses `config.yaml`.
- **Returns**: Dictionary representing the decoded raw configuration contents.
- **Side effects**: Updates `self.characters`, `self.settings`, and `self.active_character_name`.
- **Exception handling**: If file is corrupted (e.g. invalid YAML format) or missing, it logs a warning, falls back to safe default schema, and invokes `save_config()`.

### Method Signature: `save_config(self) -> None`
- **Behavior**: Serializes internal properties into YAML format and writes them to `config.yaml`.

### Method Signature: `create_character(self, name: str) -> None`
- **Parameters**:
  - `name` (string): The raw name entered by the user.
- **Behavior**:
  - Strips whitespace.
  - If stripped name is empty or invalid, raises `ValueError("Name cannot be empty.")`.
  - If name already exists in `self.characters`, raises `ValueError("Character already exists.")`.
  - Creates a new character dictionary: `{ "name": name, "levels_completed": 0, "inventory": { "flower": 0 } }`.
  - Inserts character into `self.characters`.
  - Invokes `save_config()`.

### Method Signature: `select_character(self, name: str) -> None`
- **Parameters**:
  - `name` (string): Name of existing character.
- **Behavior**:
  - Sets `self.active_character_name = name`.
  - If character name does not exist, raises `ValueError("Character not found.")`.
  - Invokes `save_config()`.

### Method Signature: `add_rewards(self, flower_count: int) -> None`
- **Parameters**:
  - `flower_count` (integer): Number of flowers collected in the successful run.
- **Behavior**:
  - Adds `flower_count` to the active character's `inventory["flower"]`.
  - Increments active character's `levels_completed` by `1`.
  - Invokes `save_config()`.

### Property Signature: `active_character(self) -> dict or None`
- **Returns**: Returns the character dict of the currently active profile, or `None` if no character is selected.

---

## 2. Kivy Screen Flow & UI State Contracts

All screens must handle state transitions cleanly based on the `ProfileManager` state.

| Event / Action | From Screen | Expected Guard / Transition |
|----------------|-------------|----------------------------|
| Application Start | - | If `active_character` is None, go to `NewCharacterScreen`. Else go to `MenuScreen`. |
| Click "New Character" (or key 'n') | `MenuScreen` / `LoadCharacterScreen` | Transition to `NewCharacterScreen`. |
| Click "Load Character" (or key 'l') | `MenuScreen` | Transition to `LoadCharacterScreen`. |
| Click "Confirm" in New Character | `NewCharacterScreen` | Validate. If OK, call `create_character()`, set active, go to `MenuScreen`. |
| Select character in list | `LoadCharacterScreen` | Call `select_character()`, go to `MenuScreen`. |
| Win distance reached | `GameScreen` | Stop game loops, call `add_rewards()`, transition to `GameWonScreen`. |
