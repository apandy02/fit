from typing import List, Optional

from pydantic import BaseModel


class OnboardingStatus(BaseModel):
    onboarding_stage: int


class ProfileCompletionRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    units: Optional[str] = None


class MeasurementsCompletionRequest(BaseModel):
    weight: float
    height_feet: int
    height_inches: int


class DietaryCompletionRequest(BaseModel):
    existing_restrictions: List[str] = []


class ActivitySelectionRequest(BaseModel):
    activity_level: str


class GoalsSelectionRequest(BaseModel):
    weight_goal: str
