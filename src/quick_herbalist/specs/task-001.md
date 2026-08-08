# Task 001: Validate `flower_count` in `add_rewards`

## Type
Bug — Missing input validation

## Description
The method `add_rewards(flower_count)` accepts any value without validation. This allows:
- **Negative numbers** (e.g. `-5`), reducing flower inventory
- **Zero** (no-op but silently accepted)
- **Non-numeric types** (strings, `None`, floats like `3.7`)

This can lead to unexpected inventory values and potential game balance issues.

## Current Code
```python
def add_rewards(self, flower_count):
    if (
        not self.active_character_name
        or self.active_character_name not in self.characters
    ):
        raise ValueError("No active character selected.")

    char = self.characters[self.active_character_name]
    char["levels_completed"] = char.get("levels_completed", 0) + 1

    if "inventory" not in char or not isinstance(char["inventory"], dict):
        char["inventory"] = {}
    char["inventory"]["flower"] = char["inventory"].get("flower", 0) + flower_count

    self.save_config()
```

## Expected Behavior
- `flower_count` must be a positive integer (`> 0`)
- Raise `ValueError` with a clear message for invalid input:
  - Negative or zero: `"flower_count must be a positive integer."`
  - Non-integer: `"flower_count must be an integer."`
  - Non-numeric: `"flower_count must be a number."`

## Proposed Fix
```python
def add_rewards(self, flower_count):
    if (
        not self.active_character_name
        or self.active_character_name not in self.characters
    ):
        raise ValueError("No active character selected.")

    if not isinstance(flower_count, int) or isinstance(flower_count, bool):
        raise ValueError("flower_count must be an integer.")
    if flower_count <= 0:
        raise ValueError("flower_count must be a positive integer.")

    char = self.characters[self.active_character_name]
    char["levels_completed"] = char.get("levels_completed", 0) + 1

    if "inventory" not in char or not isinstance(char["inventory"], dict):
        char["inventory"] = {}
    char["inventory"]["flower"] = char["inventory"].get("flower", 0) + flower_count

    self.save_config()
```

## Files Affected
- `src/quick_herbalist/profiles.py`

## Testing
- Call `add_rewards(5)` → succeeds
- Call `add_rewards(0)` → raises `ValueError`
- Call `add_rewards(-1)` → raises `ValueError`
- Call `add_rewards("five")` → raises `ValueError`
- Call `add_rewards(3.5)` → raises `ValueError`
- Call `add_rewards(True)` → raises `ValueError` (booleans are `int` subclass)
