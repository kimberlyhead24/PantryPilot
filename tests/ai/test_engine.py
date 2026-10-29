"""Tests for the PantryPilot AI engine Protocol and its I/O dataclasses."""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass

import pytest

from app.ai.engine import (
    AIIngredient,
    AIMealIdea,
    AINutrition,
    DetectedItem,
    InventoryDeduction,
    OutsideMealEstimate,
    PantryPilotAIEngine,
    ParsedItem,
)

ALL_DATACLASSES = [
    DetectedItem,
    ParsedItem,
    AIIngredient,
    AINutrition,
    AIMealIdea,
    InventoryDeduction,
    OutsideMealEstimate,
]

PROTOCOL_METHODS = [
    "detect_items",
    "parse_list",
    "generate_meals",
    "get_inventory_deductions",
    "recalculate_nutrition",
    "log_outside_meal",
    "get_combined_quantity",
]


class FakeEngine:
    """Minimal stub that satisfies PantryPilotAIEngine."""

    def detect_items(self, image_base64, category_hint=None):
        return [DetectedItem("Milk", "1", "Dairy")]

    def parse_list(self, text):
        return [ParsedItem(line, "1", "Other") for line in text.splitlines() if line]

    def generate_meals(self, *, section, people, genre, inventory_summary,
                       dislikes, preferred_ingredients, dietary_restrictions,
                       allow_non_inventory_items):
        return [AIMealIdea(f"Meal {i}", people, "photo") for i in range(3)]

    def get_inventory_deductions(self, full_inventory, used_ingredients):
        return []

    def recalculate_nutrition(self, edited_ingredients, original_servings):
        return AINutrition("100", "5g", "2g", "10g")

    def log_outside_meal(self, meal_description):
        return OutsideMealEstimate(meal_description, 1.0, AINutrition("1", "1g", "1g", "1g"))

    def get_combined_quantity(self, quantity1, quantity2):
        return f"{quantity1} + {quantity2}"


class IncompleteEngine:
    def parse_list(self, text):
        return []


@pytest.fixture
def engine() -> FakeEngine:
    return FakeEngine()


@pytest.mark.parametrize("cls", ALL_DATACLASSES)
def test_types_are_dataclasses(cls):
    assert is_dataclass(cls)


@pytest.mark.parametrize(
    "cls, args",
    [
        (DetectedItem, ("Eggs", "12", "Dairy")),
        (ParsedItem, ("Rice", "1 lb", "Grains")),
        (AIIngredient, ("Salt", "1 tsp")),
        (AINutrition, ("200", "10g", "5g", "30g")),
        (InventoryDeduction, ("1", "Milk", "0", "Empty")),
    ],
)
def test_simple_dataclasses_store_fields_in_order(cls, args):
    obj = cls(*args)
    assert tuple(getattr(obj, f.name) for f in fields(cls)) == args


def test_dataclass_equality():
    assert DetectedItem("a", "1", "b") == DetectedItem("a", "1", "b")
    assert DetectedItem("a", "1", "b") != DetectedItem("a", "2", "b")


def test_meal_idea_defaults():
    meal = AIMealIdea("Soup", 4, "bowl of soup")
    assert meal.ingredients == []
    assert meal.instructions == ""
    assert meal.nutrition_per_serving == AINutrition("0", "0g", "0g", "0g")


def test_meal_idea_defaults_not_shared_between_instances():
    a = AIMealIdea("A", 1, "p")
    b = AIMealIdea("B", 1, "p")
    a.ingredients.append(AIIngredient("Egg", "1"))
    a.nutrition_per_serving.calories = "999"
    assert b.ingredients == []
    assert b.nutrition_per_serving.calories == "0"


def test_meal_idea_serializes_nested_dataclasses():
    meal = AIMealIdea("Omelet", 2, "omelet", [AIIngredient("Egg", "3")], "Whisk.")
    data = asdict(meal)
    assert data["ingredients"] == [{"name": "Egg", "amount": "3"}]
    assert data["nutrition_per_serving"]["protein"] == "0g"


@pytest.mark.parametrize("status", ["Empty", "Low", "OK"])
def test_inventory_deduction_accepts_documented_statuses(status):
    assert InventoryDeduction("1", "Rice", "0", status).status == status


def test_outside_meal_estimate_allows_fractional_servings():
    est = OutsideMealEstimate("Pizza", 0.5, AINutrition("300", "12g", "10g", "40g"))
    assert est.total_servings == 0.5


def test_fake_engine_satisfies_protocol(engine):
    assert isinstance(engine, PantryPilotAIEngine)


def test_incomplete_engine_does_not_satisfy_protocol():
    assert not isinstance(IncompleteEngine(), PantryPilotAIEngine)


@pytest.mark.parametrize("name", PROTOCOL_METHODS)
def test_protocol_declares_method(name):
    assert callable(getattr(PantryPilotAIEngine, name))


def test_generate_meals_is_keyword_only(engine):
    with pytest.raises(TypeError):
        engine.generate_meals("Dinner", 2, "Italian", "", [], [], [], True)


def test_engine_round_trip_returns_expected_types(engine):
    assert all(isinstance(i, DetectedItem) for i in engine.detect_items("b64"))
    assert engine.parse_list("a\nb")[1].name == "b"
    meals = engine.generate_meals(
        section="Dinner", people=2, genre="Any", inventory_summary="",
        dislikes=[], preferred_ingredients=[], dietary_restrictions=[],
        allow_non_inventory_items=False,
    )
    assert 3 <= len(meals) <= 5
    assert isinstance(engine.recalculate_nutrition([], 2), AINutrition)
    assert isinstance(engine.log_outside_meal("burger"), OutsideMealEstimate)
    assert isinstance(engine.get_combined_quantity("1", "2"), str)
