from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class MealItem(BaseModel):
    title: str
    ingredients: str = ""
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float = 0.0
    vitamin_a: float = 0.0
    vitamin_c: float = 0.0
    vitamin_d: float = 0.0
    calcium: float = 0.0
    iron: float = 0.0
    potassium: float = 0.0
    sodium: float = 0.0
    creatine: float = 0.0
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
    protein: float
    carbohydrates: float
    fat: float
    fiber: float = 0.0
    vitamin_a: float = 0.0
    vitamin_c: float = 0.0
    vitamin_d: float = 0.0
    calcium: float = 0.0
    iron: float = 0.0
    potassium: float = 0.0
    sodium: float = 0.0
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



