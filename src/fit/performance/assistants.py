import ell

from fit.performance.data_models import PerformanceStats

STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]
DEFAULT_LARGE_MODEL = "gpt-4o-2024-08-06"
DEFAULT_SMALL_MODEL = "gpt-4o-mini-2024-07-18"

@ell.simple(model=DEFAULT_LARGE_MODEL)
def early_daily_performance_overview(
    daily_stats: PerformanceStats,
    activities: list,
    caloric_target: float,
    caloric_consumption: float,
    workout_trend_summary: str,
) -> str:
    """
    Analyze the user's daily performance metrics and provide personalized feedback and recommendations.

    You will receive:
    - The user's daily activity statistics including heart rate data and steps
    - A list of workouts/activities completed today
    - Their caloric target and actual consumption for the day
    - A summary of their recent workout patterns and preferences

    Provide a natural, conversational analysis that covers:
    1. Activity Target Assessment
       - Compare their achieved metrics against daily targets
       - If below target: Calculate the deficit and provide specific recommendations to make up the difference
       - Base workout suggestions on their documented exercise history and preferences
       
    2. Overexertion Check
       - If they've exceeded activity targets, emphasize the importance of recovery
       - Provide specific rest and recovery recommendations for the next day
       
    3. Caloric Balance Intervention
       - If they've exceeded their caloric target, recommend an appropriate workout
       - The workout suggestion should be calibrated to help burn the specific caloric excess
       - Consider their fitness level and exercise history when making recommendations

    Format your response as a conversational coaching message in plain text (absolutely 
    no markdown, bullet points, or special formatting) that integrates all these elements 
    while maintaining a supportive and motivational tone.
    """
    pass


@ell.simple(model=DEFAULT_LARGE_MODEL)
def late_daily_performance_overview(
    daily_stats: PerformanceStats,
    activities: list,
    caloric_target: float,
    caloric_consumption: float,
    workout_trend_summary: str,
) -> str:
    """
    Analyze the user's daily performance metrics and provide personalized feedback and recommendations.

    You will receive:
    - The user's daily activity statistics including heart rate data and steps
    - A list of workouts/activities completed today
    - Their caloric target and actual consumption for the day
    - A summary of their recent workout patterns and preferences

    Provide a natural, conversational analysis that covers:
    1. Activity Target Assessment
       - Compare their achieved metrics against daily targets
       - If below target: Calculate the deficit and provide specific recommendations to make up the difference
       - Base workout suggestions on their documented exercise history and preferences
       
    2. Overexertion Check
       - If they've exceeded activity targets, emphasize the importance of recovery
       - Provide specific rest and recovery recommendations for the next day
       
    3. Caloric Balance Intervention
       - If they've exceeded their caloric target, recommend that they either consume less
       or workout more in the future. You can suggest a new workout or an adjustment to their
       existing workout.

    Format your response as a conversational coaching message in plain text (absolutely 
    no markdown, bullet points, or special formatting) that integrates all these elements 
    while maintaining a supportive and motivational tone.
    """
    pass