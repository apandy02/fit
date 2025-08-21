from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class LoginRequest(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class User(BaseModel):
    user_id: int
    email: Optional[str] = None
    name: Optional[str] = None


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


