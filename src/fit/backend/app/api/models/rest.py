from typing import Any, Dict, List

from pydantic import BaseModel


class RestOverviewResponse(BaseModel):
    analysis: str


class RestDailyInfoResponse(BaseModel):
    recovery: Dict[str, Any] | None
    sleep: List[Dict[str, Any]] | Dict[str, Any]


