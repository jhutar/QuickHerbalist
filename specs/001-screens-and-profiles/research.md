# Research: Screen Refactor & Character Profiles

This research resolves technical design decisions for multi-screen navigation and persistent character profiles, adhering to the QuickHerbalist Constitution.

## Decision: Decoupled Profile State Management & Persistence

### Chosen Approach
A pure Python `ProfileManager` class that manages active character state and handles serialization.
- **Serialization**: Standard `PyYAML` package to load/save profile data in `config.yaml`.
- **Decoupling**: Profile management logic is entirely isolated from Kivy UI layers. This allows full unit testing without spawning a Kivy application instance or GUI environment.
- **Save Path Resolution**:
  - In production, use `App.get_running_app().user_data_dir` if Kivy is running.
  - In test suites or when Kivy is not running, fall back to a dynamic path (e.g., standard platform-specific directories via standard `os.path` and standard environment variables) or a testing mock directory.

### Rationale
- Complies with **Principle III (Maintainability and High Testability)**.
- Simplifies automated testing. Unit tests can create, edit, save, load, and switch characters simply by instantiating `ProfileManager` in standard pytest/unittest.
- Standardizes configuration schema to match specifications.

### Alternatives Considered
- **Kivy built-in Config parser**: Rejected because Kivy `Config` is INI-style, not YAML, violating FR-002.
- **Standard Library JSON/TOML**: Rejected because specification explicitly mandates YAML (`config.yaml`).
- **Heavy External Libraries (like platformdirs)**: Avoided to keep the dependencies minimal, resolving the path dynamically using standard Python `os.path` logic if Kivy app is not running.

---

## Decision: Multi-Screen Navigation & Keyboard Shortcuts

### Chosen Approach
- Utilize Kivy's standard `ScreenManager` and `Screen` APIs to define separate screens:
  - `MenuScreen`: Shows active character, lists options, supports navigation shortcuts.
  - `NewCharacterScreen`: Form to input names, performs validations, blocks invalid names.
  - `LoadCharacterScreen`: Lists all existing characters, allows selecting one.
  - `PotionsScreen`: Create potions placeholder UI, handles back to menu.
  - `GameScreen`: Holds the gameplay widget, tracks active character info.
  - `GameWonScreen`: Displays win message, adds collected flowers to active character's inventory, increments levels completed.
  - `GameOverScreen`: Displays game over status.
  - `QuitScreen`: Quit/resume prompt.
- Keyboard navigation: Implement standard shortcuts ('n', 'l', 's', 'c', 'q') bound to specific screen events.

### Rationale
- **FR-001** and **FR-004** compliant.
- `ScreenManager` is the idiomatic way in Kivy to switch screens without window recreation, preserving smooth, instantaneous transitions (**SC-002**).

---

## Decision: YAML Parser Library Choice

### Chosen Approach
Use PyYAML added to `pyproject.toml`.

### Rationale
- PyYAML is robust, standard in the Python ecosystem, and handles complex dictionary-to-document serialization natively.
- Fits AS-002 cleanly.
