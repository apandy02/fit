# Nutrition Evals

This directory contains evaluation suites for measuring and improving our nutrition-related language model prompts. Each eval provides quantitative metrics and test cases for specific nutrition analysis tasks.

## Directory Structure
```
evals/
├── data/                      # Test datasets and ground truth data
├── tests/                    # Unit tests for evaluation metrics
├── meal_breakdown_eval.py    # Meal nutrition analysis eval
├── inventory_breakdown_eval.py # Kitchen inventory parsing eval
└── recommendation_eval.py    # Meal recommendation eval
```

## Evals

### Meal Breakdown eval
Tests the accuracy of extracting nutritional information from meal descriptions:
- Macro/micronutrient identification
- Calorie consistency checking
- Ingredient parsing accuracy
- Unit and portion size accuracy

Metrics:
- `macro_calorie_consistency`: Validates caloric values match macronutrient totals
- `ingredients_score`: Measures ingredient identification accuracy
- `basic_accuracy`: Compares predicted vs reference nutrient values

### Inventory Breakdown eval
Tests parsing and categorization of kitchen inventory items:
- Item name recognition
- Unit and quantity parsing
- Category classification
- Inventory completeness

Metrics:
- `item_precision/recall`: Accuracy of item identification
- `category_accuracy`: Correct categorization of items
- `quantity_accuracy`: Accuracy of parsed quantities
- `unit_accuracy`: Correct unit identification

### Recommendation eval
Tests meal recommendation quality and constraint satisfaction:
- Target nutrient optimization
- Overall nutritional balance
- User preference alignment
- Dietary restriction compliance

Metrics:
- `target_nutrient_accuracy`: Measures optimization of specified nutrients
- `non_target_nutrient_accuracy`: Checks maintenance of other nutrient levels
- `semantic_similarity`: Evaluates alignment with user preferences

## Test Data

- `kitchen.json`: Sample kitchen inventory descriptions with ground truth parsing
- `meal_breakdowns.csv`: Meal descriptions with validated nutritional information
- `recommendations.json`: Test cases for meal recommendations with user preferences and nutritional targets

## Running Evaluations

Each eval can be run independently:

```python
python -m fit.nutrition.evals.meal_breakdown_eval
python -m fit.nutrition.evals.inventory_breakdown_eval
python -m fit.nutrition.evals.recommendation_eval
```

Results are stored in `./logdir` for tracking performance over time. 
