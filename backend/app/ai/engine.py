"""The PantryPilot AI engine Protocol and its plain-python I/O types.

Both the offline ``RuleBasedEngine`` and the ``GoogleGeminiPantryPilotEngine``
implement this Protocol. Inputs and outputs are plain dataclasses / dicts. No
HTTP request objects, FastAPI types, or environment access leak through here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class DetectedItem:
    """A grocery item detected in a pantry or fridge photo.

    Attributes:
        name: Human-readable item name, e.g. ``"Whole Milk"``.
        quantity: Free-form quantity string, e.g. ``"2 cartons"``.
        category: Storage or grocery category, e.g. ``"Dairy"``.
    """

    name: str
    quantity: str
    category: str


@dataclass
class ParsedItem:
    """A structured item parsed from a freeform pasted list.

    Attributes:
        name: Human-readable item name.
        quantity: Free-form quantity string, e.g. ``"1 lb"``.
        category: Grocery category assigned to the item.
    """

    name: str
    quantity: str
    category: str


@dataclass
class AIIngredient:
    """A single ingredient line in a generated meal.

    Attributes:
        name: Ingredient name.
        amount: Amount with units, e.g. ``"200 g"``.
    """

    name: str
    amount: str


@dataclass
class AINutrition:
    """Per-serving nutrition facts, stored as display strings.

    Attributes:
        calories: Calories per serving, e.g. ``"450"``.
        protein: Protein per serving, e.g. ``"30g"``.
        fat: Fat per serving, e.g. ``"12g"``.
        carbs: Carbohydrates per serving, e.g. ``"50g"``.
    """

    calories: str
    protein: str
    fat: str
    carbs: str


@dataclass
class AIMealIdea:
    """A meal suggestion produced by an AI engine.

    Attributes:
        meal_name: Display name of the meal.
        total_servings: Number of servings the recipe yields.
        meal_photo_prompt: Text prompt used to generate or find a meal photo.
        ingredients: Ingredients required for the meal. Defaults to an empty list.
        instructions: Cooking instructions. Defaults to an empty string.
        nutrition_per_serving: Nutrition for one serving. Defaults to zeroed
            values (``"0"``, ``"0g"``, ``"0g"``, ``"0g"``).
    """

    meal_name: str
    total_servings: int
    meal_photo_prompt: str
    ingredients: list[AIIngredient] = field(default_factory=list)
    instructions: str = ""
    nutrition_per_serving: AINutrition = field(
        default_factory=lambda: AINutrition("0", "0g", "0g", "0g")
    )


@dataclass
class InventoryDeduction:
    """An inventory item whose quantity changed after cooking.

    Attributes:
        id: Unique identifier of the inventory item.
        name: Item name.
        new_quantity: Remaining quantity after deduction.
        status: Stock level, one of ``"Empty"``, ``"Low"``, or ``"OK"``.
    """

    id: str
    name: str
    new_quantity: str
    status: str  # one of "Empty" | "Low" | "OK"


@dataclass
class OutsideMealEstimate:
    """An estimate for a meal eaten outside the app's recipes.

    Attributes:
        meal_name: Short name inferred from the description.
        total_servings: Estimated number of servings (may be fractional).
        nutrition_per_serving: Estimated nutrition for one serving.
    """

    meal_name: str
    total_servings: float
    nutrition_per_serving: AINutrition


@runtime_checkable
class PantryPilotAIEngine(Protocol):
    """Interface that every PantryPilot AI backend must implement.

    Implementations include ``RuleBasedEngine`` (offline) and
    ``GoogleGeminiPantryPilotEngine``. Callers depend only on this Protocol,
    so engines can be swapped without changing application code.
    """

    def detect_items(
        self, image_base64: str, category_hint: str | None = None
    ) -> list[DetectedItem]:
        """Scan a pantry or fridge photo for grocery items.

        Args:
            image_base64: Base64-encoded image data.
            category_hint: Optional category (e.g. ``"Fridge"``) to bias detection.

        Returns:
            The items detected in the image. Empty if none are found.
        """
        ...

    def parse_list(self, text: str) -> list[ParsedItem]:
        """Parse a freeform pasted list into structured items.

        Args:
            text: Raw list text, such as one item per line.

        Returns:
            The parsed items, in input order.
        """
        ...

    def generate_meals(
        self,
        *,
        section: str,
        people: int,
        genre: str,
        inventory_summary: str,
        dislikes: list[str],
        preferred_ingredients: list[str],
        dietary_restrictions: list[str],
        allow_non_inventory_items: bool,
    ) -> list[AIMealIdea]:
        """Generate 3-5 meal ideas from inventory and preferences.

        Args:
            section: Meal section, e.g. ``"Dinner"``.
            people: Number of people to cook for.
            genre: Cuisine or style, e.g. ``"Italian"``.
            inventory_summary: Text summary of available inventory.
            dislikes: Ingredients to avoid.
            preferred_ingredients: Ingredients to favor.
            dietary_restrictions: Restrictions such as ``"vegetarian"``.
            allow_non_inventory_items: Whether ingredients outside the
                inventory may be suggested.

        Returns:
            Between three and five meal ideas.
        """
        ...

    def get_inventory_deductions(
        self, full_inventory: list[dict], used_ingredients: list[dict]
    ) -> list[InventoryDeduction]:
        """Compute inventory changes after cooking a meal.

        Args:
            full_inventory: All current inventory items as dicts.
            used_ingredients: Ingredients consumed by the meal, as dicts.

        Returns:
            Only the inventory items whose quantity changed.
        """
        ...

    def recalculate_nutrition(
        self, edited_ingredients: list[dict], original_servings: int
    ) -> AINutrition:
        """Recompute per-serving nutrition for an edited ingredient list.

        Args:
            edited_ingredients: The updated ingredients, as dicts.
            original_servings: Number of servings the recipe yields.

        Returns:
            Updated nutrition per serving.
        """
        ...

    def log_outside_meal(self, meal_description: str) -> OutsideMealEstimate:
        """Estimate servings and nutrition for a freeform meal description.

        Args:
            meal_description: Plain-text description, e.g. ``"two slices of pizza"``.

        Returns:
            Estimated servings and per-serving nutrition.
        """
        ...

    def get_combined_quantity(self, quantity1: str, quantity2: str) -> str:
        """Merge two quantity strings for the same item.

        Args:
            quantity1: First quantity, e.g. ``"1 lb"``.
            quantity2: Second quantity, e.g. ``"8 oz"``.

        Returns:
            The combined quantity string, e.g. ``"1.5 lb"``.
        """
        ...
