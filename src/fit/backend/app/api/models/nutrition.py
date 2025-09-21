from datetime import date
from typing import Optional

from enum import Enum

from pydantic import BaseModel, Field


class NutrientUnit(Enum):
    kcal = "kcal"
    kJ = "kJ"
    g = "g"
    mg = "mg"
    ug = "ug"
    ml = "ml"
    IU = "IU"


class MealItem(BaseModel):
    title: str
    ingredients: str = ""
    calories: float
    calories_unit: NutrientUnit = NutrientUnit.kcal
    protein: float
    protein_unit: NutrientUnit = NutrientUnit.g
    carbohydrates: float
    carbohydrates_unit: NutrientUnit = NutrientUnit.g
    fat: float
    fat_unit: NutrientUnit = NutrientUnit.g
    fiber: float = 0.0
    fiber_unit: NutrientUnit = NutrientUnit.g
    vitamin_a: float = 0.0
    vitamin_a_unit: NutrientUnit = NutrientUnit.ug
    vitamin_c: float = 0.0
    vitamin_c_unit: NutrientUnit = NutrientUnit.mg
    vitamin_d: float = 0.0
    vitamin_d_unit: NutrientUnit = NutrientUnit.ug
    calcium: float = 0.0
    calcium_unit: NutrientUnit = NutrientUnit.mg
    iron: float = 0.0
    iron_unit: NutrientUnit = NutrientUnit.mg
    potassium: float = 0.0
    potassium_unit: NutrientUnit = NutrientUnit.mg
    sodium: float = 0.0
    sodium_unit: NutrientUnit = NutrientUnit.mg
    creatine: float = 0.0
    creatine_unit: NutrientUnit = NutrientUnit.g
    meal_time: str = Field(description="HH:MM")
    date_entered: Optional[date] = None


class MealLog(BaseModel):
    id: int
    meal_time: str
    item: MealItem


class AnalysisRequest(BaseModel):
    text: str


class AnalysisResult(BaseModel):
    title: str
    ingredients: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    vitamin_a: float
    vitamin_c: float
    vitamin_d: float
    calcium: float
    iron: float
    potassium: float
    sodium: float
    creatine: float


class SupplementCreate(BaseModel):
    title: str
    time_consumed: str = Field(description="HH:MM or HH:MM:SS")
    calories: float
    calories_unit: NutrientUnit = NutrientUnit.kcal
    protein: float
    protein_unit: NutrientUnit = NutrientUnit.g
    carbohydrates: float
    carbohydrates_unit: NutrientUnit = NutrientUnit.g
    fat: float
    fat_unit: NutrientUnit = NutrientUnit.g
    fiber: float = 0.0
    fiber_unit: NutrientUnit = NutrientUnit.g
    vitamin_a: float = 0.0
    vitamin_a_unit: NutrientUnit = NutrientUnit.ug
    vitamin_c: float = 0.0
    vitamin_c_unit: NutrientUnit = NutrientUnit.mg
    vitamin_d: float = 0.0
    vitamin_d_unit: NutrientUnit = NutrientUnit.ug
    calcium: float = 0.0
    calcium_unit: NutrientUnit = NutrientUnit.mg
    iron: float = 0.0
    iron_unit: NutrientUnit = NutrientUnit.mg
    potassium: float = 0.0
    potassium_unit: NutrientUnit = NutrientUnit.mg
    sodium: float = 0.0
    sodium_unit: NutrientUnit = NutrientUnit.mg
    date_entered: Optional[date] = None


class SupplementLogRequest(BaseModel):
    supplement_name: str
    time_consumed: str = Field(description="HH:MM or HH:MM:SS")
    servings: float = 1.0
    date_entered: Optional[date] = None


class WaterLogRequest(BaseModel):
    amount_ml: float = Field(description="Water consumed in milliliters")
    time_consumed: str = Field(description="HH:MM or HH:MM:SS")
    date_entered: Optional[date] = None


class RegenerateAnalysisRequest(BaseModel):
    feedback: str
    # Original breakdown from previous analysis
    original_breakdown: dict
