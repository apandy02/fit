"""Utility functions for converting between units."""

from enum import Enum


class NutrientUnit(Enum):
    kcal = "kcal"
    kJ = "kJ"
    g = "g"
    mg = "mg"
    ug = "ug"
    IU = "IU"


def convert_nutrient_unit(value: float, from_unit: NutrientUnit, to_unit: NutrientUnit) -> float:
    """Convert a value from one unit to another."""
    if from_unit == to_unit:
        return value
    if from_unit == NutrientUnit.kcal and to_unit == NutrientUnit.kJ:
        return (value * 4.184)
    if from_unit == NutrientUnit.kJ and to_unit == NutrientUnit.kcal:
        return (value / 4.184)
    if from_unit == NutrientUnit.g and to_unit == NutrientUnit.mg:
        return value * 1000
    if from_unit == NutrientUnit.mg and to_unit == NutrientUnit.g:
        return value / 1000
    if from_unit == NutrientUnit.ug and to_unit == NutrientUnit.mg:
        return value / 1000
    if from_unit == NutrientUnit.mg and to_unit == NutrientUnit.ug:
        return value * 1000


def lbs_to_kg(lbs: float) -> float:
    return lbs * 0.453592

def kg_to_lbs(kg: float) -> float:
    return kg * 2.20462

def ml_to_oz(ml: float) -> float:
    return ml * 0.033814

def oz_to_ml(oz: float) -> float:
    return oz * 29.5735
