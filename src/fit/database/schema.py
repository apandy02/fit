from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    email: str
    provider: str
    provider_user_id: str

@dataclass
class Meal:
    date_entered: str
    ingredients: str
    meal_time: str
    user_description: str
    llm_summary: str
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
    is_supplement: bool
    user_id: int

@dataclass
class Supplement:
    user_id: int
    name: str
    description: str
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

@dataclass
class Measurement:
    datetime: str
    height: float
    weight: float
    user_id: int

@dataclass
class Water:
    date: str
    user_id: int
    time: str
    water_consumed_ml: float

@dataclass
class Profile:
    user_id: int
    name: str
    email: str
    gender: str
    date_of_birth: str
    units: str
    dietary_restrictions: str
    activity_level: str
    weight_goal: float
    fitness_goal: str
    onboarding_stage: int

@dataclass
class Inventory:
    user_id: int
    title: str
    quantity: float
    unit: str
    category: str

@dataclass
class SupplementEntry:
    user_id: int
    supplement_name: str
    date_consumed: str
    time_consumed: str
    servings: float
