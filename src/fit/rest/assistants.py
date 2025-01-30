from datetime import datetime

import ell

from fit.nutrition.data_models import MealBreakdown

# TODO: find some central place to store these (they are currently maintained in multiple places)
STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]
DEFAULT_LARGE_MODEL = "gpt-4o-2024-08-06"
DEFAULT_SMALL_MODEL = "gpt-4o-mini-2024-07-18"

@ell.simple(model=DEFAULT_LARGE_MODEL)
def analyze_rest_patterns(
      sleep_data: list[dict],
      meals: list[tuple[datetime, MealBreakdown]],
      activities: list[tuple[datetime, str, float]],
      sleep_targets: dict[str, float],
      recovery_metrics: dict[str, float]
   ) -> str:
   system_message = """
   Analyze the user's rest and recovery patterns in relation to their daily activities and habits.

   Provide a comprehensive analysis that covers:
   1. Sleep Target Assessment
      - Compare actual sleep metrics against targets
      - Identify patterns of over/under sleeping
      - Analyze sleep quality metrics and their trends
   2. Meal Impact Analysis
      - Identify correlations between meal timing/content and sleep quality
      - Flag potentially disruptive eating patterns (late meals, heavy dinners)
      - Suggest optimal meal timing and composition for better rest
   3. Activity Impact Analysis
      - Evaluate how workout timing affects sleep quality
      - Identify signs of overtraining or insufficient recovery
      - Analyze relationship between activity intensity and recovery metrics
   4. Recovery Status
      - Interpret HRV and resting heart rate trends
      - Assess overall recovery status
      - Provide specific recommendations for improving recovery

   Format your response as a conversational coaching message in plain text (absolutely 
   no markdown, bullet points, or special formatting) that integrates all these elements 
   while maintaining a supportive and educational tone. Focus on actionable insights 
   and specific recommendations for improvement.
   """
   user_string = f"""
   Here is my sleep data: {sleep_data}\n, Here are my meals: {meals}\n
   Here are my activities: {activities}\n, Here are my sleep targets: {sleep_targets}\n
   Here are my recovery metrics: {recovery_metrics}
   """
   return [
      ell.system(system_message),
      ell.user(user_string)
   ]
