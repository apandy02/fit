import ell 
from fit.nutrition.data_models import MealBreakdown
from fit.performance.data_models import PerformanceStats


STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]
DEFAULT_LARGE_MODEL = "gpt-4o-2024-08-06"
DEFAULT_SMALL_MODEL = "gpt-4o-mini-2024-07-18"

@ell.simple(model=DEFAULT_LARGE_MODEL)
def daily_performance_overview(
    daily_stats: PerformanceStats,
    activities: list,
    consumption: list[MealBreakdown],
    workout_trend_summary: str,
    consumption_target: dict,
) -> str:
    """
    I want to take in what the user's daily activity target was. 

    What they ended up achieving. 

    The workouts they did. 

    How they did on their nutrition (over or under caloric targets)

    I want to give them feedback along the following axes:
    - did they hit their activity target? If not, how much did they miss by? what could they have done to improve?
       - Personalize this recommendation based on workouts from their past. 
    - did they exceed their activity target? If so, recommend increased rest for the next day.
    - if they exceeded their caloric target, and it is not too late in the day,
    recommend a workout that will help them burn off the excess calories.
    """
    pass