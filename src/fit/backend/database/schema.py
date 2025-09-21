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
    # unit fields
    calories_unit: str
    protein_unit: str
    carbohydrates_unit: str
    fat_unit: str
    fiber_unit: str
    vitamin_a_unit: str
    vitamin_c_unit: str
    vitamin_d_unit: str
    calcium_unit: str
    iron_unit: str
    potassium_unit: str
    sodium_unit: str
    creatine_unit: str
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
    # unit fields
    calories_unit: str
    protein_unit: str
    carbohydrates_unit: str
    fat_unit: str
    fiber_unit: str
    vitamin_a_unit: str
    vitamin_c_unit: str
    vitamin_d_unit: str
    calcium_unit: str
    iron_unit: str
    potassium_unit: str
    sodium_unit: str


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
    supplement_id: int
    date_consumed: str
    time_consumed: str
    servings: float


@dataclass
class TrackerAccount:
    user_id: int
    provider: str
    provider_user_id: str
    access_token: str
    refresh_token: str | None
    expires_at: str | None
    scopes: str | None
    primary: bool
    linked_at: str


@dataclass
class OAuthState:
    state: str
    code_verifier: str
    provider: str
    user_id: int | None
    redirect_to: str | None
    created_at: str
    expires_at: str
