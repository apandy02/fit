from typing import Any, Dict, List

from pydantic import BaseModel


class PerformanceOverviewRequest(BaseModel):
    tracker: str
    access_token: str


class PerformanceOverviewResponse(BaseModel):
    analysis: str


class PerformanceDailyInfoResponse(BaseModel):
    daily_stats: Dict[str, Any]
    workouts: List[dict]
