from typing import Optional

from pydantic import BaseModel


class PerformanceStats(BaseModel):
    """
    A model that contains the user's performance stats for a given day.
    """

    max_heart_rate: float
    min_heart_rate: float
    avg_heart_rate: float
    total_calories_burned: float
    steps_walked: Optional[float]
