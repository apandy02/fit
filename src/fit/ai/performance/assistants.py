# src/fit/ai/performance/assistants.py
import datetime

from pydantic_ai import Agent

from fit.ai.performance.data_models import PerformanceStats

STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]
DEFAULT_LARGE_MODEL = "gpt-4o-2024-08-06"
DEFAULT_SMALL_MODEL = "gpt-4o-mini-2024-07-18"

def _agent(model: str, system_prompt: str) -> Agent:
   return Agent(f"openai:{model}", system_prompt=system_prompt)

def early_daily_performance_overview(
      daily_stats: PerformanceStats,
      activities: list,
      caloric_target: float,
      caloric_consumption: float,
      workout_trend_summary: str,
      time: datetime.time,
      time_cutoff: datetime.time,
   ) -> str:
   if time.hour < time_cutoff.hour:
      workout_recommendation_string = """
      - If they've exceeded their caloric target, recommend an appropriate workout
      - The workout suggestion should be calibrated to help burn the specific caloric excess
      - Consider their fitness level and exercise history when making recommendations
      """
   else:
      workout_recommendation_string = """
      - If they've exceeded their caloric target, recommend that they either consume less
      - or workout more in the future. You can suggest a new workout or an adjustment to their
      - existing workout.
      """
   system_message = f"""
   You are a digital health and fitness assistant.
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
      {workout_recommendation_string}

    Format your response as a conversational coaching message in plain text (absolutely 
    no markdown, bullet points, or special formatting) that integrates all these elements 
    while maintaining a professional tone.
    avoid all salutations and be to the point. 
    """
   user_string = f"""
   Here are my daily stats: {daily_stats}\n, Here are my activities: {activities}\n
   Here is my caloric target: {caloric_target}\n, Here is my caloric consumption: {caloric_consumption}\n
   Here is my workout trend summary: {workout_trend_summary}
   """
   agent = _agent(DEFAULT_LARGE_MODEL, system_message)
   res = agent.run(user_string)
   return res.text

def summarize_workout_trends(workouts: list) -> str:
    system = """
    Summarize the user's workout trends and provide a summary of their recent workout patterns and preferences.
    Return a concise plain-text summary.
    """
    agent = _agent(DEFAULT_SMALL_MODEL, system)
    res = agent.run(f"Here is the user's workout log: {workouts}")
    return res.text
