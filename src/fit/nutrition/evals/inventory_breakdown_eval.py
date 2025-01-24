import json
import logging
import os
from typing import Dict, List

import ell
import numpy as np

from fit.nutrition.assistants import decipher_inventory
from fit.nutrition.data_models import KitchenInventory, KitchenItem

ell.init(store="./logdir")

DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"

def prepare_eval_data():
    """Load and prepare the kitchen inventory evaluation data."""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    kitchen_path = os.path.join(data_dir, "kitchen.json")
    with open(kitchen_path, "r") as f:
        data = json.load(f)
    
    dataset = []

    for item in data["data"]:
        # Convert outputs to KitchenItem objects for type safety
        dataset.append({
            "input": item["input"],
            "reference": KitchenInventory.model_validate(item["outputs"])
        })
    
    return dataset

def calculate_item_metrics(prediction: List[KitchenItem], reference: List[KitchenItem]) -> Dict[str, float]:
    """Calculate precision and recall for item names."""
    pred_names = set(item.name.lower() for item in prediction)
    ref_names = set(item.name.lower() for item in reference)
    
    true_positives = len(pred_names.intersection(ref_names))
    false_positives = len(pred_names - ref_names)
    false_negatives = len(ref_names - pred_names)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    return {
        "precision": precision,
        "recall": recall
    }

def category_accuracy_metric(prediction: List[KitchenItem], reference: List[KitchenItem]) -> float:
    """Calculate accuracy of category assignments for correctly identified items."""
    correct_categories = 0
    total_matches = 0
    
    pred_items = {item.name.lower(): item for item in prediction}
    ref_items = {item.name.lower(): item for item in reference}
    
    common_items = set(pred_items.keys()) & set(ref_items.keys())
    if not common_items:
        return 0.0
        
    for item_name in common_items:
        total_matches += 1
        if pred_items[item_name].category == ref_items[item_name].category:
            correct_categories += 1
            
    return correct_categories / total_matches if total_matches > 0 else 0.0

def quantity_accuracy_metric(prediction: List[KitchenItem], reference: List[KitchenItem]) -> float:
    """Calculate accuracy of quantity predictions for correctly identified items."""
    quantity_errors = []
    
    pred_items = {item.name.lower(): item for item in prediction}
    ref_items = {item.name.lower(): item for item in reference}
    
    common_items = set(pred_items.keys()) & set(ref_items.keys())
    if not common_items:
        return 0.0
        
    for item_name in common_items:
        pred_qty = pred_items[item_name].quantity
        ref_qty = ref_items[item_name].quantity
        if ref_qty != 0:
            error = abs(pred_qty - ref_qty) / ref_qty
            quantity_errors.append(error)
        
    return 1 - np.mean(quantity_errors) if quantity_errors else 0.0

def unit_accuracy_metric(prediction: List[KitchenItem], reference: List[KitchenItem]) -> float:
    """Calculate accuracy of unit predictions for correctly identified items."""
    correct_units = 0
    total_matches = 0
    
    pred_items = {item.name.lower(): item for item in prediction}
    ref_items = {item.name.lower(): item for item in reference}
    
    common_items = set(pred_items.keys()) & set(ref_items.keys())
    if not common_items:
        return 0.0
        
    for item_name in common_items:
        total_matches += 1
        if pred_items[item_name].unit.lower() == ref_items[item_name].unit.lower():
            correct_units += 1
            
    return correct_units / total_matches if total_matches > 0 else 0.0

if __name__ == "__main__":
    dataset = prepare_eval_data()
    
    def item_metrics_wrapper(prediction, reference):
        metrics = calculate_item_metrics(prediction, reference)
        return metrics["precision"]
    
    def recall_wrapper(prediction, reference):
        metrics = calculate_item_metrics(prediction, reference)
        return metrics["recall"]

    def inventory_wrapper(input_text):
        """Wrapper to handle inventory prediction."""
        inventory = decipher_inventory(input_text)
        return inventory.items

    eval = ell.evaluation.Evaluation(
        name="inventory_breakdown_eval",
        dataset=dataset,
        metrics={
            "precision": item_metrics_wrapper,
            "recall": recall_wrapper,
            "category_accuracy": category_accuracy_metric,
            "quantity_accuracy": quantity_accuracy_metric,
            "unit_accuracy": unit_accuracy_metric
        }
    )
    
    result = eval.run(inventory_wrapper)

    logging.info("Average Precision:", result.results.metrics["precision"].mean())
    logging.info("Average Recall:", result.results.metrics["recall"].mean())
    logging.info("Average Category Accuracy:", result.results.metrics["category_accuracy"].mean())
    logging.info("Average Quantity Accuracy:", result.results.metrics["quantity_accuracy"].mean())
    logging.info("Average Unit Accuracy:", result.results.metrics["unit_accuracy"].mean())
