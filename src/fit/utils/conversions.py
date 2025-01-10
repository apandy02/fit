"""Utility functions for converting between units."""

def kcal_to_kj(kcal: float) -> float:
    """Convert kilocalories to kilojoules."""
    return kcal * 4.184

def kj_to_kcal(kj: float) -> float:
    """Convert kilojoules to kilocalories."""
    return kj / 4.184

def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms."""
    return lbs * 0.453592

def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462

def ml_to_oz(ml: float) -> float:
    """Convert milliliters to ounces."""
    return ml * 0.033814

def oz_to_ml(oz: float) -> float:
    """Convert ounces to milliliters."""
    return oz * 29.5735