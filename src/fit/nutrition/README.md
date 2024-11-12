# Nutrition

This subdirectory contains all of the code related to nutrition management.

## Structure

The following is the structure of the subdirectory:

- `__init__.py`
- `data.py`: contains the data definitions for the nutrition tracking system.
- `assistants.py`: contains the assistant definitions for the nutrition tracking system. These are the entities that interact with the user via language model calls. 

## Language Model Tooling

This project uses `ell` for language model interaction and abstraction. Ell provides a clean interface through decorators and message handling that enables:

- Simple text-based LLM calls via `@ell.simple`
- Structured outputs with `@ell.complex` 
- Built-in versioning and tracing
- Type-safe message handling

The assistants in `assistants.py` are implemented as Language Model Programs (LMPs) using ell's decorators and APIs.

## Example Usage

### Using the Nutrition Assistants

```python
from fit.nutrition.assistants import NutritionTracker, FoodAssistant
from fit.nutrition.data import Goals, NutritionalInfo

# Initialize the nutrition tracker
tracker = NutritionTracker()

# Track nutrition from text description
breakfast = tracker.natural_language_macros(
    "2 scrambled eggs with 2 slices of whole wheat toast and an apple"
)
print(f"Breakfast macros:")
print(f"Calories: {breakfast.calories}")
print(f"Protein: {breakfast.protein}g")
print(f"Carbs: {breakfast.carbs}g")
print(f"Fat: {breakfast.fat}g")

# Track nutrition from an image
lunch_image_path = "path/to/lunch_image.jpg"
lunch = tracker.image_macros(lunch_image_path)
print(f"\nLunch macros:")
print(f"Calories: {lunch.calories}")
print(f"Protein: {lunch.protein}g")
print(f"Carbs: {lunch.carbs}g")
print(f"Fat: {lunch.fat}g")

# Get food recommendations based on goals and intake
assistant = FoodAssistant()

# Example daily stats
daily_burn = 2500  # calories
current_intake = NutritionalInfo(
    calories=1200,
    protein=60,
    carbs=150,
    fat=40
)

# Get recommendations for muscle gain
recommendations = assistant.make_recommendations(
    caloric_burn=daily_burn,
    goal=Goals.MUSCLE_GAIN,
    prior_intake=current_intake
)
print("\nRecommended meals:")
print(recommendations)
```

Example output:
```
Breakfast macros:
Calories: 420
Protein: 20g
Carbs: 54g
Fat: 16g

Lunch macros:
Calories: 650
Protein: 35g
Carbs: 75g
Fat: 22g

Recommended meals:
1. Grilled chicken breast (8oz) with sweet potato and broccoli
2. Protein smoothie with banana, whey protein, and peanut butter
3. Greek yogurt parfait with granola and mixed berries
```
