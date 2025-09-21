from typing import List, Optional

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    units: Optional[str] = None
    dietary_restrictions: List[str] = Field(default_factory=list)
    activity_level: Optional[str] = None
    weight_goal: Optional[str] = None
    fitness_goal: Optional[str] = None
    onboarding_stage: Optional[int] = None


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    units: Optional[str] = None
    dietary_restrictions: List[str] = Field(default_factory=list)
    activity_level: Optional[str] = None
    weight_goal: Optional[str] = None
    fitness_goal: Optional[str] = None
    onboarding_stage: Optional[int] = None


class RestrictionChangeRequest(BaseModel):
    restriction: str
    existing_restrictions: List[str] = Field(default_factory=list)


class RestrictionListResponse(BaseModel):
    restrictions: List[str]
