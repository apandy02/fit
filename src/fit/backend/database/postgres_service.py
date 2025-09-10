from __future__ import annotations

from datetime import datetime

import fit.ai.nutrition.data_models as dm
from .pg import get_engine
from fit.backend.database.repositories.profile import ProfileRepository
from fit.backend.database.repositories.meals import MealsRepository
from fit.backend.database.repositories.inventory import InventoryRepository
from fit.backend.database.repositories.supplements import SupplementsRepository
from fit.backend.database.repositories.water import WaterRepository
from fit.backend.database.repositories.measurements import MeasurementsRepository
from fit.backend.database.repositories.accounts import AccountsRepository


class PostgresDatabaseService:
    def __init__(self):
        self._engine = get_engine()
        # repositories
        self.profile_repo = ProfileRepository(self._engine)
        self.meals_repo = MealsRepository(self._engine)
        self.inventory_repo = InventoryRepository(self._engine)
        self.supplements_repo = SupplementsRepository(self._engine)
        self.water_repo = WaterRepository(self._engine)
        self.measurements_repo = MeasurementsRepository(self._engine)
        self.accounts_repo = AccountsRepository(self._engine)

    def ensure_local_user(self, user_id: int) -> None:
        """Ensure a user row exists for local/dev logins."""
        self.accounts_repo.ensure_local_user(user_id)

    def get_user_id(self, provider_user_id: str, provider: str) -> int | None:
        return self.accounts_repo.get_user_id(provider_user_id, provider)

    def insert_new_user(self, user_dict: dict) -> int:
        return self.accounts_repo.insert_new_user(user_dict)

    def get_profile_data(self, user_id: int) -> dict:
        return self.profile_repo.get_profile_data(user_id)

    def get_dietary_restrictions(self, user_id: int):
        return self.profile_repo.get_dietary_restrictions(user_id)

    def insert_profile(self, form_data: dict) -> bool:
        return self.profile_repo.insert_profile(form_data)

    def update_profile(self, form_data: dict) -> bool:
        return self.profile_repo.update_profile(form_data)

    def get_daily_meals(self, date: datetime, user_id: int) -> list[dict]:
        return self.meals_repo.get_daily_meals(date, user_id)

    def get_all_meal_summaries(self, user_id: int):
        return self.meals_repo.get_all_meal_summaries(user_id)

    def get_daily_cumulative_nutrition(self, date: datetime, user_id: int) -> dm.NutritionalInformation:
        return self.meals_repo.get_daily_cumulative_nutrition(date, user_id)

    def insert_meal(
        self,
        meal_description: str,
        meal: dm.MealBreakdown | dm.NutritionalInformation,
        meal_date: str,
        meal_time: str,
        user_id: int,
        summary: str | None = None,
        ingredients: str | None = None,
        is_supplement: bool = False,
    ):
        self.meals_repo.insert_meal(
            meal_description,
            meal,
            meal_date,
            meal_time,
            user_id,
            summary,
            ingredients,
            is_supplement,
        )

    def delete_meal(self, meal_id: int) -> bool:
        return self.meals_repo.delete_meal(meal_id)

    def insert_supplement(self, name: str, consumption_time: str, nutritional_info: dm.NutritionalInformation, date: str, user_id: int):
        self.supplements_repo.insert_supplement(name, nutritional_info, user_id)
        # also log as a meal for now
        self.meals_repo.insert_meal(name, nutritional_info, date, consumption_time, user_id, is_supplement=True)

    def get_supplement(self, name: str, user_id: int) -> dm.NutritionalInformation | None:
        return self.supplements_repo.get_supplement(name, user_id)

    def get_supplement_names(self, user_id: int) -> list[str]:
        return self.supplements_repo.get_supplement_names(user_id)

    def log_supplement_consumption(self, user_id: int, supplement_name: str, servings: float, time_consumed: str):
        self.supplements_repo.log_supplement_consumption(user_id, supplement_name, servings, time_consumed)

    def get_all_supplements(self, user_id: int) -> list[tuple[str, str, dm.NutritionalInformation]]:
        return self.supplements_repo.get_all_supplements(user_id)

    def get_daily_supplement_entries(self, user_id: int, date: datetime) -> list[tuple[str, float, str]]:
        return self.supplements_repo.get_daily_supplement_entries(user_id, date)

    def insert_water_consumption(self, water_consumed_ml: float, date_consumed: datetime, time_consumed: str, user_id: int):
        self.water_repo.insert_water_consumption(water_consumed_ml, date_consumed, time_consumed, user_id)

    def get_daily_water_consumption(self, date: datetime, user_id: int) -> float:
        return self.water_repo.get_daily_water_consumption(date, user_id)

    def get_user_measurements(self, user_id: int):
        return self.measurements_repo.get_user_measurements(user_id)

    def get_latest_user_measurements(self, user_id: int) -> dict | None:
        return self.measurements_repo.get_latest_user_measurements(user_id)

    def insert_user_measurements(self, height: float, weight: float, dt: datetime, user_id: int):
        self.measurements_repo.insert_user_measurements(height, weight, dt, user_id)

    def insert_measurement(self, user_id: int, weight: float, date: datetime, height: float) -> bool:
        return self.measurements_repo.insert_measurement(user_id, weight, date, height)

    def insert_inventory_item(self, title: str, quantity: float, unit: str, category: str, user_id: int):
        self.inventory_repo.insert_inventory_item(title, quantity, unit, category, user_id)

    def get_inventory(self, user_id: int) -> dict:
        return self.inventory_repo.get_inventory(user_id)

    def get_weight_goal(self, user_id: int) -> str:
        return self.profile_repo.get_weight_goal(user_id)

    def delete_inventory_item(self, rowid: int) -> bool:
        return self.inventory_repo.delete_inventory_item(rowid)

    def create_oauth_state(self, state: str, code_verifier: str, provider: str, user_id: int | None, redirect_to: str | None, created_at: str, expires_at: str):
        self.accounts_repo.create_oauth_state(state, code_verifier, provider, user_id, redirect_to, created_at, expires_at)

    def consume_oauth_state(self, state: str) -> dict | None:
        return self.accounts_repo.consume_oauth_state(state)

    def upsert_tracker_account(self, user_id: int, provider: str, provider_user_id: str, access_token: str, refresh_token: str | None, expires_at: str | None, scopes: str | None, primary: bool = False):
        self.accounts_repo.upsert_tracker_account(user_id, provider, provider_user_id, access_token, refresh_token, expires_at, scopes, primary)

    def get_tracker_account(self, user_id: int, provider: str | None = None, primary_only: bool = True) -> dict | None:
        return self.accounts_repo.get_tracker_account(user_id, provider, primary_only)

    def list_tracker_accounts(self, user_id: int) -> list[dict]:
        return self.accounts_repo.list_tracker_accounts(user_id)

    def set_primary_tracker(self, user_id: int, provider: str):
        self.accounts_repo.set_primary_tracker(user_id, provider)

    def update_tracker_tokens(self, user_id: int, provider: str, access_token: str, refresh_token: str | None, expires_at: str | None):
        self.accounts_repo.update_tracker_tokens(user_id, provider, access_token, refresh_token, expires_at)


