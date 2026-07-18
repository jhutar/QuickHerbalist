# Quickstart & Validation Guide: Screen Refactor & Character Profiles

This guide provides step-by-step procedures to manually and automatically validate the screens refactor and persistent character profile system.

## Prerequisites
- **Python**: 3.11+ environment.
- **UV**: Standard dependency and runtime manager.
- Install project dependencies including Kivy and PyYAML:
  ```bash
  uv sync
  ```

---

## 1. Automated Validation (Unit Tests)

Run the isolated unit test suite to verify the `ProfileManager` state machine and file persistence operations without spawning any GUI window.

```bash
# Execute unit tests using pytest or python -m unittest
uv run pytest tests/
```

### Expected Output
- All profile validation, fallback, corruption handling, and creation tests pass.
- No Kivy GUI window spawned.

---

## 2. Manual End-to-End Validation

### Scenario A: First Run & Profile Creation
1. Delete any existing profile files:
   - Linux: `rm -f ~/.config/quickherbalist/config.yaml` or relevant Kivy user data directory.
2. Start the game application:
   - Command: `uv run quick-herbalist` (or `python -m quick_herbalist`)
3. **Verify**: App launches directly into the **New Character** screen (skipping Main Menu because no profile exists).
4. **Action**: Attempt to click "Confirm" with an empty name or whitespace name.
   - **Verify**: App shows a warning or disables confirmation.
5. **Action**: Type name `HerbalistMax` and click "Confirm" (or press enter).
   - **Verify**: Screen switches instantly to the **Main Menu**.
   - **Verify**: The text in the Menu header shows: `Active: HerbalistMax`.
   - **Verify**: Under `~/.config/quickherbalist/` (or platform equivalent), `config.yaml` is written with correct keys.

### Scenario B: Game Win & Inventory Update
1. On the **Main Menu** screen, click "Start Game" or press `s`.
2. Play the game run until the target distance of 1000.0 is completed.
   - **Verify**: Game transitions instantly to the **Game Won** screen showing "Level Completed!".
3. Check the `config.yaml` file.
   - **Verify**: `levels_completed` has incremented to `1`, and `inventory["flower"]` has been added/updated with the collected flowers count.

### Scenario C: Profile Loading
1. Relaunch the application.
   - **Verify**: Automatically loads active character `HerbalistMax` on start, displaying it on the Main Menu.
2. Click "New Character" or press `n`. Create `AnotherHero`.
   - **Verify**: Active character is now `AnotherHero`.
3. Click "Load Character" or press `l`. Select `HerbalistMax` from the listed profiles.
   - **Verify**: App switches back to Main Menu showing `Active: HerbalistMax` as selected profile.
