import os
import yaml
import pytest
from quick_herbalist.profiles import ProfileManager

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
            "inventory": {"flower": 20}
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
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert data["active_character"] is None

def test_profile_manager_partial_missing_fields_recovery(temp_config_dir):
    # Save a configuration with missing settings and characters keys
    config_path = os.path.join(temp_config_dir, "config.yaml")
    os.makedirs(temp_config_dir, exist_ok=True)
    
    data = {
        "active_character": "MissingKeysHero"
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
        
    pm = ProfileManager(config_dir=temp_config_dir)
    
    # Assert it falls back gracefully for individual missing components
    assert pm.active_character_name == "MissingKeysHero"
    assert pm.settings["fps"] == 60
    assert pm.characters == {}
