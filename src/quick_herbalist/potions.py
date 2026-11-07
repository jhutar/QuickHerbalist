"""Potion brewing domain: recipe loading, validation, and recipe matching."""

from dataclasses import dataclass, field

import yaml

# Number of potion slots a player can bring into the next run.
RUN_SLOT_COUNT = 3


class RecipeError(ValueError):
    """Domain error raised when the recipes file is invalid."""


@dataclass
class Recipe:
    """A single potion recipe with its exact ingredient requirements."""

    id: str
    name_key: str
    description_key: str
    ingredients: dict = field(default_factory=dict)
    duration_seconds: float = 0.0


def _validate_positive_int(value, where) -> None:
    """Raise RecipeError unless value is a positive int (bool excluded)."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RecipeError(f"{where} must be a positive integer, got {value!r}")


def load_recipes(path, valid_ingredients=None):
    """Load and validate recipes from a YAML file, fail-fast on any bad entry.

    valid_ingredients, when given, is the set of allowed ingredient (sprite)
    names; unknown names are load errors.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or not isinstance(data.get("recipes"), list):
        raise RecipeError("recipes file must contain a top-level 'recipes' list")

    recipes = []
    seen_ids = set()
    for index, entry in enumerate(data["recipes"]):
        if not isinstance(entry, dict):
            raise RecipeError(f"recipe #{index} must be a mapping")
        for key in ("id", "name_key", "description_key"):
            value = entry.get(key)
            if not isinstance(value, str) or not value:
                raise RecipeError(f"recipe #{index} is missing a valid '{key}'")
        recipe_id = entry["id"]
        if recipe_id in seen_ids:
            raise RecipeError(f"duplicate recipe id '{recipe_id}'")
        seen_ids.add(recipe_id)

        ingredients = entry.get("ingredients")
        if not isinstance(ingredients, dict) or not ingredients:
            raise RecipeError(f"recipe '{recipe_id}' needs a non-empty 'ingredients' mapping")
        for sprite_name, count in ingredients.items():
            if not isinstance(sprite_name, str) or not sprite_name:
                raise RecipeError(f"recipe '{recipe_id}' has an invalid ingredient name")
            if valid_ingredients is not None and sprite_name not in valid_ingredients:
                raise RecipeError(f"recipe '{recipe_id}' uses unknown ingredient '{sprite_name}'")
            _validate_positive_int(count, f"recipe '{recipe_id}' ingredient count")

        duration = entry.get("duration_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            raise RecipeError(f"recipe '{recipe_id}' duration_seconds must be a positive number")

        recipes.append(
            Recipe(
                id=recipe_id,
                name_key=entry["name_key"],
                description_key=entry["description_key"],
                ingredients=dict(ingredients),
                duration_seconds=float(duration),
            )
        )
    return recipes


def match_recipe(content, recipes):
    """Return the recipe whose ingredients exactly match the cauldron content.

    Matching is an order-independent exact multiset equality; extra, missing,
    or over-counted ingredients all yield None.
    """
    clean = {name: count for name, count in (content or {}).items() if count and count > 0}
    for recipe in recipes:
        if clean == recipe.ingredients:
            return recipe
    return None
