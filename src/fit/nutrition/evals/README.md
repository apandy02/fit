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

- **Meal Breakdown eval**: Tests the accuracy of extracting nutritional information from meal descriptions.
- **Inventory Breakdown eval**: Tests parsing and categorization of kitchen inventory items.
- **Recommendation eval**: Tests meal recommendation quality and constraint satisfaction.
- **Inventory completeness eval**: Tests the completeness of the kitchen inventory. 

## Data

Datasets for each eval are stored in the `data` directory. 

Results for evals are stored in `./logdir` for tracking performance over time. 

We can use the ell-studio tool to visualize and better understand eval results. 

Run ell studio as follows:

```
ell-studio --storage ./logdir
```

## Running Evaluations

Each eval can be run independently:

```python
python -m fit.nutrition.evals.meal_breakdown_eval
python -m fit.nutrition.evals.inventory_breakdown_eval
python -m fit.nutrition.evals.recommendation_eval
```


