from __future__ import annotations

from fit.backend.database.pg import get_engine
from fit.backend.database.repositories.meals import MealsRepository
from fit.backend.database.repositories.profile import ProfileRepository
from fit.backend.database.repositories.inventory import InventoryRepository
from fit.backend.database.repositories.supplements import SupplementsRepository
from fit.backend.database.repositories.water import WaterRepository
from fit.backend.database.repositories.measurements import MeasurementsRepository
from fit.backend.database.repositories.accounts import AccountsRepository


class Database:
    def __init__(self):
        engine = get_engine()
        self.meals = MealsRepository(engine)
        self.profile = ProfileRepository(engine)
        self.inventory = InventoryRepository(engine)
        self.supplements = SupplementsRepository(engine)
        self.water = WaterRepository(engine)
        self.measurements = MeasurementsRepository(engine)
        self.accounts = AccountsRepository(engine)
