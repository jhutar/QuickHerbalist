import os

import pytest
import yaml

from quick_herbalist.profiles import ProfileError, ProfileErrorCode, ProfileManager


@pytest.fixture
def temp_config_dir(tmp_path):
    return str(tmp_path)


def test_profile_manager_init_default(temp_config_dir):
    # Setup manager
    pm = ProfileManager(config_dir=temp_config_dir)

    # Assert directory and default config file are created
    assert os.path.exists(pm.config_path)

    # Verify default state values
    assert pm.active_character_name is None
    assert pm.settings["fps"] == 60
    assert pm.settings["win_distance"] == 1000.0
    assert pm.settings["game_speed_start"] == 3.0
    assert pm.characters == {}
    assert pm.active_character is None


def test_profile_manager_save_and_load(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    # Manually modify values
    pm.active_character_name = "HerbalistMax"
    pm.settings["fps"] = 120
    pm.characters = {
        "HerbalistMax": {
            "name": "HerbalistMax",
            "levels_completed": 3,
            "inventory": {"flower": 20},
        }
    }

    # Save modification
    pm.save_config()

    # Instantiate new ProfileManager to read from same config
    pm2 = ProfileManager(config_dir=temp_config_dir)

    # Assert values loaded match saved values
    assert pm2.active_character_name == "HerbalistMax"
    assert pm2.settings["fps"] == 120
    assert pm2.characters["HerbalistMax"]["levels_completed"] == 3
    assert pm2.characters["HerbalistMax"]["inventory"]["flower"] == 20
    assert pm2.active_character == pm2.characters["HerbalistMax"]


def test_profile_manager_fallback_on_corrupt_yaml(temp_config_dir):
    # Create corrupted config.yaml
    config_path = os.path.join(temp_config_dir, "config.yaml")
    os.makedirs(temp_config_dir, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("{invalid: yaml: parsing: error:")

    pm = ProfileManager(config_dir=temp_config_dir)

    # Assert values fallback to default structure safely instead of crashing
    assert pm.active_character_name is None
    assert pm.settings["fps"] == 60
    assert pm.characters == {}

    # Assert valid yaml written on fallback recovery
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert data["active_character"] is None


def test_profile_manager_partial_missing_fields_recovery(temp_config_dir):
    # Save a configuration with missing settings and characters keys
    config_path = os.path.join(temp_config_dir, "config.yaml")
    os.makedirs(temp_config_dir, exist_ok=True)

    data = {"active_character": "MissingKeysHero"}
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)

    pm = ProfileManager(config_dir=temp_config_dir)

    # Assert it falls back gracefully for individual missing components
    assert pm.active_character_name == "MissingKeysHero"
    assert pm.settings["fps"] == 60
    assert pm.characters == {}


# --- User Story 1 (US1) Test Cases ---


def test_profile_manager_create_character_success(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    # Create valid character
    pm.create_character("HerbalistMax")

    # Assert it is saved in characters dictionary with default values
    assert "HerbalistMax" in pm.characters
    char = pm.characters["HerbalistMax"]
    assert char["name"] == "HerbalistMax"
    assert char["levels_completed"] == 0
    assert char["inventory"] == {}

    # Assert it is set as the active character
    assert pm.active_character_name == "HerbalistMax"
    assert pm.active_character == char

    # Assert saved to file
    pm2 = ProfileManager(config_dir=temp_config_dir)
    assert "HerbalistMax" in pm2.characters
    assert pm2.active_character_name == "HerbalistMax"


def test_profile_manager_create_character_validations(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    # Rejects empty name
    with pytest.raises(ProfileError) as exc_info:
        pm.create_character("")
    assert exc_info.value.code is ProfileErrorCode.EMPTY_NAME

    # Rejects whitespace-only name
    with pytest.raises(ProfileError) as exc_info:
        pm.create_character("   ")
    assert exc_info.value.code is ProfileErrorCode.EMPTY_NAME

    # Rejects None name
    with pytest.raises(ProfileError) as exc_info:
        pm.create_character(None)
    assert exc_info.value.code is ProfileErrorCode.EMPTY_NAME

    # Rejects duplicate name
    pm.create_character("UniqueName")
    with pytest.raises(ProfileError) as exc_info:
        pm.create_character("UniqueName")
    assert exc_info.value.code is ProfileErrorCode.DUPLICATE_CHARACTER

    # Rejects duplicate name with leading/trailing whitespaces (since it gets stripped)
    with pytest.raises(ProfileError) as exc_info:
        pm.create_character(" UniqueName ")
    assert exc_info.value.code is ProfileErrorCode.DUPLICATE_CHARACTER


def test_profile_manager_select_character_success(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("Hero1")
    pm.create_character("Hero2")

    # Select Hero1
    pm.select_character("Hero1")
    assert pm.active_character_name == "Hero1"
    assert pm.active_character["name"] == "Hero1"

    # Select Hero2
    pm.select_character("Hero2")
    assert pm.active_character_name == "Hero2"
    assert pm.active_character["name"] == "Hero2"


def test_profile_manager_select_character_not_found(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    # Select non-existent character
    with pytest.raises(ProfileError) as exc_info:
        pm.select_character("FakeHero")
    assert exc_info.value.code is ProfileErrorCode.CHARACTER_NOT_FOUND


# --- User Story 2 (US2) Test Cases ---


def test_profile_manager_complete_level_no_active_character(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    with pytest.raises(ProfileError) as exc_info:
        pm.complete_level()
    assert exc_info.value.code is ProfileErrorCode.NO_ACTIVE_CHARACTER


def test_profile_manager_add_flowers_no_active_character(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("dandelion_sprite", 10)
    assert exc_info.value.code is ProfileErrorCode.NO_ACTIVE_CHARACTER


def test_profile_manager_add_flowers_invalid_flower_count(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("HerbalistMax")

    # Reject negative
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("dandelion_sprite", -1)
    assert exc_info.value.code is ProfileErrorCode.INVALID_FLOWER_COUNT

    # Reject string
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("dandelion_sprite", "five")
    assert exc_info.value.code is ProfileErrorCode.INVALID_FLOWER_COUNT

    # Reject float
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("dandelion_sprite", 3.5)
    assert exc_info.value.code is ProfileErrorCode.INVALID_FLOWER_COUNT

    # Reject None
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("dandelion_sprite", None)
    assert exc_info.value.code is ProfileErrorCode.INVALID_FLOWER_COUNT

    # Reject boolean
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("dandelion_sprite", True)
    assert exc_info.value.code is ProfileErrorCode.INVALID_FLOWER_COUNT


def test_profile_manager_add_flowers_invalid_sprite_name(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("HerbalistMax")

    # Reject empty string
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers("", 5)
    assert exc_info.value.code is ProfileErrorCode.INVALID_SPRITE_NAME

    # Reject non-string
    with pytest.raises(ProfileError) as exc_info:
        pm.add_flowers(None, 5)
    assert exc_info.value.code is ProfileErrorCode.INVALID_SPRITE_NAME


def test_profile_manager_complete_level_success(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("HerbalistMax")

    pm.complete_level()
    char = pm.characters["HerbalistMax"]
    assert char["levels_completed"] == 1

    pm.complete_level()
    assert char["levels_completed"] == 2

    pm2 = ProfileManager(config_dir=temp_config_dir)
    char2 = pm2.characters["HerbalistMax"]
    assert char2["levels_completed"] == 2


def test_profile_manager_add_flowers_success(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("HerbalistMax")

    # Zero is valid (winning a level without collecting flowers)
    pm.add_flowers("dandelion_sprite", 0)
    assert pm.characters["HerbalistMax"]["inventory"]["dandelion_sprite"] == 0

    pm.add_flowers("dandelion_sprite", 5)
    char = pm.characters["HerbalistMax"]
    assert char["inventory"]["dandelion_sprite"] == 5

    # A second flower type accumulates separately
    pm.add_flowers("bluebell_sprite", 3)
    assert char["inventory"]["bluebell_sprite"] == 3

    pm.add_flowers("dandelion_sprite", 12)
    assert char["inventory"]["dandelion_sprite"] == 17
    assert char["inventory"]["bluebell_sprite"] == 3

    pm2 = ProfileManager(config_dir=temp_config_dir)
    char2 = pm2.characters["HerbalistMax"]
    assert char2["inventory"]["dandelion_sprite"] == 17
    assert char2["inventory"]["bluebell_sprite"] == 3


def test_next_level_number_no_active_character(temp_config_dir):
    # Without an active character the next level is 1
    pm = ProfileManager(config_dir=temp_config_dir)
    assert pm.next_level_number() == 1


def test_next_level_number_tracks_completions(temp_config_dir):
    # Next level is levels_completed + 1 for the active character
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    assert pm.next_level_number() == 1
    pm.complete_level()
    pm.complete_level()
    assert pm.next_level_number() == 3


def test_playable_level_numbers_no_active_character(temp_config_dir):
    # Without an active character only level 1 is playable
    pm = ProfileManager(config_dir=temp_config_dir)
    assert pm.playable_level_numbers() == [1]


def test_playable_level_numbers_tracks_completions(temp_config_dir):
    # Completed levels stay playable plus the next level
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    assert pm.playable_level_numbers() == [1]
    pm.complete_level()
    pm.complete_level()
    assert pm.playable_level_numbers() == [1, 2, 3]


def test_playable_level_numbers_capped_by_max_levels(temp_config_dir):
    # Playable list never exceeds the number of configured levels
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    pm.complete_level()
    pm.complete_level()
    assert pm.playable_level_numbers(max_levels=2) == [1, 2]


def _pm_with_character(temp_config_dir):
    """Create a profile manager with one active character."""
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    return pm


def test_new_character_has_potion_keys(temp_config_dir):
    # New characters start with empty potions, cauldron and 3 empty run slots
    pm = _pm_with_character(temp_config_dir)

    char = pm.active_character
    assert char["potions"] == {}
    assert char["cauldron"] == {}
    assert char["run_loadout"] == [None, None, None]


def test_add_and_get_potion(temp_config_dir):
    # Adding potions accumulates counts per potion id
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")
    pm.add_potion("potion_magnetism", 2)

    assert pm.get_potions() == {"potion_magnetism": 3}
    assert pm.get_potion_count("potion_magnetism") == 3
    assert pm.get_potion_count("potion_other") == 0


def test_add_potion_requires_active_character(temp_config_dir):
    # Adding potions without an active character fails fast
    pm = ProfileManager(config_dir=temp_config_dir)

    with pytest.raises(ProfileError) as exc:
        pm.add_potion("potion_magnetism")
    assert exc.value.code == ProfileErrorCode.NO_ACTIVE_CHARACTER


def test_add_potion_rejects_bad_id(temp_config_dir):
    # Empty or non-string potion ids are rejected
    pm = _pm_with_character(temp_config_dir)

    for bad in ("", 5, None):
        with pytest.raises(ProfileError) as exc:
            pm.add_potion(bad)
        assert exc.value.code == ProfileErrorCode.INVALID_POTION_ID


def test_consume_potion(temp_config_dir):
    # Consuming decrements the count and drops the key at zero
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism", 2)
    pm.consume_potion("potion_magnetism")
    assert pm.get_potion_count("potion_magnetism") == 1
    pm.consume_potion("potion_magnetism")
    assert pm.get_potion_count("potion_magnetism") == 0
    assert pm.get_potions() == {}


def test_consume_potion_not_enough(temp_config_dir):
    # Consuming more than held fails fast
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")

    with pytest.raises(ProfileError) as exc:
        pm.consume_potion("potion_magnetism", 2)
    assert exc.value.code == ProfileErrorCode.NOT_ENOUGH_POTIONS
    assert pm.get_potion_count("potion_magnetism") == 1


def test_move_flower_to_cauldron(temp_config_dir):
    # Moving a flower decrements inventory and increments the cauldron
    pm = _pm_with_character(temp_config_dir)
    pm.add_flowers("dandelion_sprite", 2)
    pm.move_flower_to_cauldron("dandelion_sprite")

    assert pm.get_inventory() == {"dandelion_sprite": 1}
    assert pm.get_cauldron() == {"dandelion_sprite": 1}


def test_move_flower_to_cauldron_not_enough(temp_config_dir):
    # Moving a flower the character does not hold fails fast
    pm = _pm_with_character(temp_config_dir)

    with pytest.raises(ProfileError) as exc:
        pm.move_flower_to_cauldron("dandelion_sprite")
    assert exc.value.code == ProfileErrorCode.NOT_ENOUGH_FLOWERS
    assert pm.get_cauldron() == {}


def test_move_cauldron_ingredient_back(temp_config_dir):
    # Removing from the cauldron returns the unit to the inventory
    pm = _pm_with_character(temp_config_dir)
    pm.add_flowers("dandelion_sprite", 2)
    pm.move_flower_to_cauldron("dandelion_sprite")
    pm.move_cauldron_ingredient_to_inventory("dandelion_sprite")

    assert pm.get_inventory() == {"dandelion_sprite": 2}
    assert pm.get_cauldron() == {}


def test_move_cauldron_ingredient_back_not_in_cauldron(temp_config_dir):
    # Removing an ingredient the cauldron does not hold fails fast
    pm = _pm_with_character(temp_config_dir)

    with pytest.raises(ProfileError) as exc:
        pm.move_cauldron_ingredient_to_inventory("dandelion_sprite")
    assert exc.value.code == ProfileErrorCode.NOT_IN_CAULDRON


def test_clear_cauldron(temp_config_dir):
    # Clearing empties the cauldron; the ingredients are lost
    pm = _pm_with_character(temp_config_dir)
    pm.add_flowers("dandelion_sprite", 2)
    pm.move_flower_to_cauldron("dandelion_sprite")
    pm.move_flower_to_cauldron("dandelion_sprite")
    pm.clear_cauldron()

    assert pm.get_cauldron() == {}
    assert pm.get_inventory() == {}


def test_assign_potion_to_first_free_slot(temp_config_dir):
    # Assigning without an index takes the first free slot and costs a potion
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")
    pm.assign_potion_to_slot("potion_magnetism")

    assert pm.get_run_loadout() == ["potion_magnetism", None, None]
    assert pm.get_potion_count("potion_magnetism") == 0


def test_assign_same_potion_to_all_slots(temp_config_dir):
    # The same potion type may fill all three slots, costing one each
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism", 3)
    for _ in range(3):
        pm.assign_potion_to_slot("potion_magnetism")

    assert pm.get_run_loadout() == ["potion_magnetism"] * 3
    assert pm.get_potion_count("potion_magnetism") == 0


def test_assign_potion_to_specific_slot(temp_config_dir):
    # Assigning with an index targets that slot when it is free
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")
    pm.assign_potion_to_slot("potion_magnetism", slot_index=2)

    assert pm.get_run_loadout() == [None, None, "potion_magnetism"]


def test_assign_potion_slot_taken(temp_config_dir):
    # Assigning into an occupied slot fails fast
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism", 2)
    pm.assign_potion_to_slot("potion_magnetism")

    with pytest.raises(ProfileError) as exc:
        pm.assign_potion_to_slot("potion_magnetism", slot_index=0)
    assert exc.value.code == ProfileErrorCode.RUN_SLOT_TAKEN
    assert pm.get_potion_count("potion_magnetism") == 1


def test_assign_potion_no_free_slot(temp_config_dir):
    # Filling the last slot then assigning again fails fast
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism", 4)
    for _ in range(3):
        pm.assign_potion_to_slot("potion_magnetism")

    with pytest.raises(ProfileError) as exc:
        pm.assign_potion_to_slot("potion_magnetism")
    assert exc.value.code == ProfileErrorCode.NO_FREE_RUN_SLOT
    assert pm.get_potion_count("potion_magnetism") == 1


def test_assign_potion_bad_slot_index(temp_config_dir):
    # Out-of-range or non-int slot indices are rejected
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")

    for bad in (-1, 3, "0", True):
        with pytest.raises(ProfileError) as exc:
            pm.assign_potion_to_slot("potion_magnetism", slot_index=bad)
        assert exc.value.code == ProfileErrorCode.INVALID_SLOT_INDEX


def test_release_run_slot(temp_config_dir):
    # Releasing a slot returns the potion to the potions inventory
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")
    pm.assign_potion_to_slot("potion_magnetism")
    pm.release_run_slot(0)

    assert pm.get_run_loadout() == [None, None, None]
    assert pm.get_potion_count("potion_magnetism") == 1


def test_release_run_slot_empty(temp_config_dir):
    # Releasing an empty slot fails fast
    pm = _pm_with_character(temp_config_dir)

    with pytest.raises(ProfileError) as exc:
        pm.release_run_slot(0)
    assert exc.value.code == ProfileErrorCode.RUN_SLOT_EMPTY


def test_use_run_slot_consumes_potion(temp_config_dir):
    # Using a slot empties it permanently; the potion is not returned to inventory
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism", 2)
    pm.assign_potion_to_slot("potion_magnetism")
    pm.use_run_slot(0)

    assert pm.get_run_loadout() == [None, None, None]
    assert pm.get_potion_count("potion_magnetism") == 1


def test_use_run_slot_persists(temp_config_dir):
    # An emptied slot stays empty across a save/load cycle
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism", 2)
    pm.assign_potion_to_slot("potion_magnetism", slot_index=2)
    pm.use_run_slot(2)

    pm2 = ProfileManager(config_dir=temp_config_dir)
    pm2.select_character("herb")
    assert pm2.get_run_loadout() == [None, None, None]
    assert pm2.get_potion_count("potion_magnetism") == 1


def test_use_run_slot_empty(temp_config_dir):
    # Using an empty slot fails fast
    pm = _pm_with_character(temp_config_dir)

    with pytest.raises(ProfileError) as exc:
        pm.use_run_slot(0)
    assert exc.value.code == ProfileErrorCode.RUN_SLOT_EMPTY


def test_use_run_slot_bad_slot_index(temp_config_dir):
    # Out-of-range or non-int slot indices are rejected
    pm = _pm_with_character(temp_config_dir)
    pm.add_potion("potion_magnetism")
    pm.assign_potion_to_slot("potion_magnetism")

    for bad in (-1, 3, "0", True):
        with pytest.raises(ProfileError) as exc:
            pm.use_run_slot(bad)
        assert exc.value.code == ProfileErrorCode.INVALID_SLOT_INDEX


def test_potions_loadout_cauldron_persist_round_trip(temp_config_dir):
    # Potions, run loadout and cauldron survive a save/load cycle
    pm = _pm_with_character(temp_config_dir)
    pm.add_flowers("dandelion_sprite", 2)
    pm.move_flower_to_cauldron("dandelion_sprite")
    pm.add_potion("potion_magnetism", 2)
    pm.assign_potion_to_slot("potion_magnetism", slot_index=1)

    pm2 = ProfileManager(config_dir=temp_config_dir)
    pm2.select_character("herb")

    assert pm2.get_cauldron() == {"dandelion_sprite": 1}
    assert pm2.get_inventory() == {"dandelion_sprite": 1}
    assert pm2.get_potions() == {"potion_magnetism": 1}
    assert pm2.get_run_loadout() == [None, "potion_magnetism", None]


def test_old_save_without_potion_keys_migrates(temp_config_dir):
    # Pre-potion saves load with potion keys backfilled
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    pm.active_character_name = None
    del pm.characters["herb"]["potions"]
    del pm.characters["herb"]["run_loadout"]
    del pm.characters["herb"]["cauldron"]
    pm.save_config()

    pm2 = ProfileManager(config_dir=temp_config_dir)
    pm2.select_character("herb")

    assert pm2.get_potions() == {}
    assert pm2.get_run_loadout() == [None, None, None]
    assert pm2.get_cauldron() == {}


def test_create_character_sets_hint_keys(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("herb")

    char = pm.characters["herb"]
    assert char["show_hints"] is True
    assert char["seen_entities"] == []


def test_create_character_can_disable_hints(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    pm.create_character("herb", show_hints=False)

    assert pm.characters["herb"]["show_hints"] is False
    assert pm.hints_enabled() is False


def test_old_save_without_hint_keys_migrates(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    del pm.characters["herb"]["seen_entities"]
    del pm.characters["herb"]["show_hints"]
    pm.save_config()

    pm2 = ProfileManager(config_dir=temp_config_dir)
    pm2.select_character("herb")

    assert pm2.hints_enabled() is True
    assert pm2.get_seen_entities() == []


def test_mark_entity_seen_round_trip(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)
    pm.create_character("herb")
    pm.mark_entity_seen("stone")
    pm.mark_entity_seen("stone")  # duplicate: no double entry, no error
    pm.mark_entity_seen("hill")

    pm2 = ProfileManager(config_dir=temp_config_dir)
    pm2.select_character("herb")

    assert pm2.get_seen_entities() == ["stone", "hill"]


def test_hint_accessors_without_active_character(temp_config_dir):
    pm = ProfileManager(config_dir=temp_config_dir)

    assert pm.hints_enabled() is True
    assert pm.get_seen_entities() == []
    pm.mark_entity_seen("stone")  # no-op, must not raise
