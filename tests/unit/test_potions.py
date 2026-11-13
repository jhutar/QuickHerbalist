"""Tests for potion recipe loading, validation, and recipe matching."""

import pytest
import yaml

from quick_herbalist.potions import (
    RUN_SLOT_COUNT,
    Recipe,
    RecipeError,
    load_recipes,
    match_recipe,
)


def _write_recipes(tmp_path, data):
    """Write recipe data to a yaml file and return its path."""
    path = tmp_path / "recipes.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return str(path)


def _valid_recipe_data():
    """Return a minimal valid recipes payload."""
    return {
        "recipes": [
            {
                "id": "potion_magnetism",
                "name_key": "potion_magnetism_name",
                "description_key": "potion_magnetism_description",
                "ingredients": {"dandelion_sprite": 2, "bluebell_sprite": 1},
                "duration_seconds": 30,
            }
        ]
    }


def test_load_recipes_valid(tmp_path):
    """A valid file loads into Recipe objects with preserved fields."""
    recipes = load_recipes(_write_recipes(tmp_path, _valid_recipe_data()))

    assert len(recipes) == 1
    recipe = recipes[0]
    assert isinstance(recipe, Recipe)
    assert recipe.id == "potion_magnetism"
    assert recipe.name_key == "potion_magnetism_name"
    assert recipe.description_key == "potion_magnetism_description"
    assert recipe.ingredients == {"dandelion_sprite": 2, "bluebell_sprite": 1}
    assert recipe.duration_seconds == 30.0


def test_load_recipes_rejects_missing_top_level_list(tmp_path):
    """A file without a top-level 'recipes' list is a load error."""
    with pytest.raises(RecipeError):
        load_recipes(_write_recipes(tmp_path, {"nope": []}))


def test_load_recipes_rejects_duplicate_id(tmp_path):
    """Two recipes with the same id are a load error."""
    data = _valid_recipe_data()
    data["recipes"].append(dict(data["recipes"][0]))
    with pytest.raises(RecipeError, match="duplicate"):
        load_recipes(_write_recipes(tmp_path, data))


@pytest.mark.parametrize("key", ["id", "name_key", "description_key"])
def test_load_recipes_rejects_missing_key(tmp_path, key):
    """Any missing required string key is a load error."""
    data = _valid_recipe_data()
    del data["recipes"][0][key]
    with pytest.raises(RecipeError):
        load_recipes(_write_recipes(tmp_path, data))


@pytest.mark.parametrize("count", [0, -1, 1.5, "2", True])
def test_load_recipes_rejects_bad_ingredient_count(tmp_path, count):
    """Ingredient counts must be positive ints, nothing else."""
    data = _valid_recipe_data()
    data["recipes"][0]["ingredients"] = {"dandelion_sprite": count}
    with pytest.raises(RecipeError):
        load_recipes(_write_recipes(tmp_path, data))


def test_load_recipes_rejects_empty_ingredients(tmp_path):
    """A recipe without ingredients is a load error."""
    data = _valid_recipe_data()
    data["recipes"][0]["ingredients"] = {}
    with pytest.raises(RecipeError):
        load_recipes(_write_recipes(tmp_path, data))


def test_load_recipes_rejects_unknown_ingredient(tmp_path):
    """An ingredient name not in valid_ingredients is a load error."""
    data = _valid_recipe_data()
    data["recipes"][0]["ingredients"] = {"flower3_sprite": 1}
    with pytest.raises(RecipeError, match="unknown ingredient"):
        load_recipes(_write_recipes(tmp_path, data), valid_ingredients={"dandelion_sprite"})


def test_load_recipes_accepts_known_ingredient(tmp_path):
    """An ingredient name in valid_ingredients passes."""
    data = _valid_recipe_data()
    data["recipes"][0]["ingredients"] = {"dandelion_sprite": 2}
    recipes = load_recipes(_write_recipes(tmp_path, data), valid_ingredients={"dandelion_sprite"})
    assert recipes[0].ingredients == {"dandelion_sprite": 2}


@pytest.mark.parametrize("duration", [0, -5, "30", None, True])
def test_load_recipes_rejects_bad_duration(tmp_path, duration):
    """Duration must be a positive number, nothing else."""
    data = _valid_recipe_data()
    data["recipes"][0]["duration_seconds"] = duration
    with pytest.raises(RecipeError):
        load_recipes(_write_recipes(tmp_path, data))


def _recipe(ingredients):
    """Build a Recipe directly for matching tests."""
    return Recipe(
        id="potion_magnetism",
        name_key="potion_magnetism_name",
        description_key="potion_magnetism_description",
        ingredients=ingredients,
        duration_seconds=30.0,
    )


def test_match_recipe_exact_match():
    """Exact multiset equality matches, regardless of dict order."""
    recipes = [_recipe({"dandelion_sprite": 2, "bluebell_sprite": 1})]
    content = {"bluebell_sprite": 1, "dandelion_sprite": 2}

    assert match_recipe(content, recipes) is recipes[0]


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        ({"dandelion_sprite": 2, "bluebell_sprite": 2}, "extra_ingredient_unit"),
        ({"dandelion_sprite": 1}, "missing_ingredient_unit"),
        ({"dandelion_sprite": 2, "bluebell_sprite": 1, "flower3_sprite": 1}, "unknown_ingredient"),
        ({}, "empty_cauldron"),
    ],
)
def test_match_recipe_no_match(content, reason):
    """Any deviation from the recipe multiset (extra/missing/unknown/empty) means no match."""
    recipes = [_recipe({"dandelion_sprite": 2, "bluebell_sprite": 1})]

    assert match_recipe(content, recipes) is None


def test_match_recipe_zero_counts_ignored():
    """Zero-count entries in the cauldron content are ignored."""
    recipes = [_recipe({"dandelion_sprite": 2})]

    assert match_recipe({"dandelion_sprite": 2, "bluebell_sprite": 0}, recipes) is recipes[0]


def test_match_recipe_no_recipes():
    """With no recipes defined nothing ever matches."""
    assert match_recipe({"dandelion_sprite": 2}, []) is None


def test_run_slot_count_is_three():
    """The run loadout has exactly three slots."""
    assert RUN_SLOT_COUNT == 3
