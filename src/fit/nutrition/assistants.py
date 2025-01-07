from datetime import datetime

import ell
from PIL import Image

from fit.nutrition.data import (MealBreakdown, NutritionalInformation,
                                NutritionFeedback, Recommendations)

STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]

class NutritionLogger:
    """A class that uses LLMs to help with nutrition tracking."""
    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        """
        Args:
            model: The LLM to use.
        """
        self.model = model

    def natural_language_macros(self, food: str) -> MealBreakdown:
        """Returns the macro nutrients in grams and kilocalories for food described in plain text.
        Args:
            food: The food to get the macro nutrients for.
        """
        @ell.complex(model=self.model, response_format=MealBreakdown)
        def _natural_language_macros(food: str) -> MealBreakdown:
            """given what the user ate, return the macro nutrients in grams.
            If the user query is not food, return 0 for all macros.
            """
            return food
        
        message = _natural_language_macros(food)
        return message.content[0].parsed
    
    def improve_breakdown(self, breakdown: MealBreakdown, user_feedback: str) -> MealBreakdown:
        """Improves the breakdown based on user feedback."""
        @ell.complex(model=self.model, response_format=MealBreakdown)
        def _improve_breakdown(breakdown: MealBreakdown, user_feedback: str) -> MealBreakdown:
            """
            Given the user's feedback on your prediction of the breakdown of their meal,
            improve the breakdown.
            """
            prompt = f"""
            The user's feedback on your prediction of the breakdown of their meal is: {user_feedback}
            The breakdown of the meal is: {breakdown}
            """
            return prompt
        
        message = _improve_breakdown(breakdown, user_feedback)
        return message.content[0].parsed
    
    def image_macros(self, image: Image.Image, additional_context: str) -> MealBreakdown:
        """Returns the macro nutrients in grams and kilocalories for food described in an image.
        Args:
            image: The image to get the macro nutrients for.
        """
        @ell.complex(model=self.model, response_format=MealBreakdown)
        def _image_macros(image: Image.Image, additional_context: str) -> MealBreakdown:
            system_message = """
            given an image of what the user ate, return the macro nutrients in grams.
            If the image is not food, return 0 for all macros. The user may or may not
            provide additional context about the food. If they do, use it to improve your
            prediction.
            """
            return [
                ell.system(system_message),
                ell.user([additional_context, image]),
            ]
        
        message = _image_macros(image, additional_context)
        return message.content[0].parsed


class Nutritionist:
    """A class that uses LLMs recommend foods. Based on the user's caloric burn and macro goals."""
    def __init__(self, model: str = "gpt-4o-2024-08-06", max_tokens: int = 2048):
        """
        Args:
            model: The LLM to use.
        """
        self.model = model
        self.max_tokens = max_tokens
    
    def summarize_user_preferences(self, meals: list[MealBreakdown]) -> str:
        """Analyzes a list of meals to summarize the user's dietary preferences and patterns."""
        @ell.complex(model=self.model, max_tokens=200)
        def _summarize_user_preferences(meals: list[MealBreakdown]) -> str:
            """Given a list of meals the user has eaten, analyze their dietary preferences and patterns.
            For example: "The user frequently eats Indian food, and seems to consume chicken as their 
            primary protein. They also seem to like yogurt."

            Focus on identifying:
            - Cuisine preferences
            - Common protein (and other major nutrients) sources (if any)
            - Common ingredients or food combinations
            - Any apparent dietary restrictions
            """
            prompt = f"""
            Here are the meals the user has eaten: {meals}
            Please analyze their dietary preferences and patterns.
            """
            return prompt

        message = _summarize_user_preferences(meals)
        return message.content[0].text

    def make_recommendations(
            self, consumption: NutritionalInformation,
            targets: NutritionalInformation,
            target_nutrient: str,
            user_preferences: str,
            restrictions: list[str]
        ) -> Recommendations:
        """Makes recommendations for foods based on the user's caloric burn and macro goals.
        Args:
            caloric_burn: The user's caloric burn for the day.
            goal: The user's weight goals.
            prior_intake: The user's prior intake for the day.
            target_nutrient: The nutrient the user is trying to improve.
            user_preferences: The user's dietary preferences and patterns.
            restrictions: The user's dietary restrictions.
        """
        @ell.complex(model=self.model, response_format=Recommendations)
        def _make_recommendations(
                consumption: NutritionalInformation,
                targets: NutritionalInformation,
                target_nutrient: str,
                user_preferences: str,
                restrictions: list[str]
            ) -> Recommendations:
            """You will be given the user's consumed nutritional information, their nutritional targets,
            their dietary restrictions, and a specific nutrient they are asking you for food recommendations to 
            improve.

            You will also be given a summary of the user's dietary preferences and patterns. The list of meals
            you return should contain 3 meals that take this information into account. 
            The others should be exploratory in that they attempt to get the user to try new things.

            Considering all the other nutrient info, try and provide the user with suggestions that 
            minimize risk of over/under consumption of other.

            For example, if the user is asking for food recommendations to improve their vitamin_c intake,
            but they already have a high carbohydrate intake, suggest a vitamin_c rich food that is low in 
            carbohydrates.

            Make sure that the suggestions are serving aware. if the user is 30g of protein under their target,
            it does not make sense to suggest a meal with 100g of chicken, this would be excessive.
            """
            user_input = f"""
            User Preferences: {user_preferences}
            Consumption: {str(consumption)}
            Targets: {str(targets)}
            Dietary Restrictions: {restrictions}
            They want trying to improve their {target_nutrient} intake.
            """
            return user_input
        
        return _make_recommendations(
            consumption, targets, target_nutrient, user_preferences, restrictions
        ).content[0].parsed
    
    def daily_io_analysis(self, meals: list[MealBreakdown], target: dict[str, float], restrictions: list[str]) -> NutritionFeedback:
        """
        Analyzes the user's daily intake and target and produces an overview with feedback.

        Args:
            meals: The user's meals for the day.
            target: The user's target for the day.
        """
        if len(meals) == 0:
            return "No meals logged for today, please log your meals and try again." # TODO: Error message is different type than expected output
        sys_message = """
        Analyze the user's daily nutritional intake versus their targets and provide a detailed assessment. 

        In the summary, talk about the caloric balance, and provide a high level overview of the
        user's nutrition (if they are highly lacking (or over) in some of them, point out that they are, and
        if they're doing well in some of them (around their target), point that out as well).

        For each of the nutrient sections, start with an overview comparing total intake to goals.
        Then evaluate each meal. Discuss any meals that contribute to to any excess or are not nutrititious
        enough if a target is underperformed on. flag meals that significantly exceed targets (e.g., >100% of
        a macro target in one meal) as problematic and suggest alternatives. if it is not too late in the day
        (roughly speaking before 8PM) and they have consumed more calories than their calorie target, suggest a
        workout that get them closer to a target range.
        
        For meals contributing to excess but not extreme, recommend portion adjustments.
        For under-target scenarios, suggest realistic additions based on their evident food preferences,
        eating patterns, and strictly following their dietary restrictions.

        Format all fields as plain text paragraphs. You must not use markdown, bullet points, or 
        special formatting, you are speaking to the user directly as their nutritionist.
        """ # TODO: the workout bit needs to go, it does not fit in here like this (too much logic hardcoding)
        #TODO: the system message can be parsed in as an arg
        current_time = datetime.now().time()
        meals_str = f"As of {current_time} are the meals the user has logged today:\n"
        
        for _, meal in enumerate(meals, 1):
            meals_str += f"""Meal {meal.title} - {meal.calories} calories, 
            {meal.macronutrients.protein}g protein, {meal.macronutrients.carbohydrates}g carbs, 
            {meal.macronutrients.fat}g fat\n
            Micros: {meal.micronutrients.vitamin_a}IU vit A, {meal.micronutrients.vitamin_c}mg vit C, 
            {meal.micronutrients.iron}mg iron, {meal.micronutrients.calcium}mg calcium, 
            {meal.micronutrients.sodium}mg sodium, {meal.micronutrients.potassium}mg potassium\n
        """
        
        targets_str = f"""
            The user's daily targets are: Calories: {target["calories"]}, Protein: {target["protein"]}g,
            Carbohydrates: {target["carbs"]}g, Fat: {target["fat"]}g
            Micronutrient targets: Vitamin A: {target["vitamin_a"]}IU, Vitamin C: {target["vitamin_c"]}mg,
            Iron: {target["iron"]}mg, Calcium: {target["calcium"]}mg,
            Sodium: {target["sodium"]}mg, Potassium: {target["potassium"]}mg
        """
        restrictions_str = f"The user's dietary restrictions are: {restrictions}"
        
        @ell.complex(model=self.model, response_format=NutritionFeedback, max_tokens=self.max_tokens)
        def _daily_io_analysis_pydantic(sys_message: str, meals_str: str, targets_str: str, restrictions_str: str) -> NutritionFeedback:
            return [
                ell.system(sys_message),
                ell.user([meals_str, targets_str, restrictions_str])
            ]
        
        @ell.simple(model=self.model, max_tokens=self.max_tokens)
        def _daily_io_analysis_simple(sys_message: str, meals_str: str, targets_str: str, restrictions_str: str) -> str:
            sys_message += f"You must absolutely respond in this format as a json string with no exceptions: {NutritionFeedback.model_json_schema()}"
            return [
                ell.system(sys_message),
                ell.user([meals_str, targets_str, restrictions_str])
            ]

        if self.model in STRUCTURED_MODELS:
            print(self.model, STRUCTURED_MODELS)
            return _daily_io_analysis_pydantic(sys_message, meals_str, targets_str, restrictions_str).content[0].parsed
        else:
            return NutritionFeedback.model_validate_json(
                _daily_io_analysis_simple(sys_message, meals_str, targets_str, restrictions_str)
            )

    def weekly_io_analysis(
            self, 
            meals: dict[datetime, list[MealBreakdown]],
            target: dict[str, float],
            restrictions: list[str]
    ) -> NutritionFeedback:
        """
        Analyzes the user's weekly intake and target and produces an overview with feedback.

        Args:
            meals: The user's meals for the week, stored per day.
            target: The user's target for the week, stored per day.
        """
        if len(meals) == 0:
            return "No meals logged for today, please log your meals and try again."
        
        @ell.complex(model=self.model, response_format=NutritionFeedback)
        def _weekly_io_analysis_pydantic(
                sys_message: str,
                meals_str: str,
                targets_str: str,
                restrictions_str: str
        ) -> NutritionFeedback:
            return [
                ell.system(sys_message),
                ell.user([meals_str, targets_str, restrictions_str])
            ]
        
        @ell.simple(model=self.model, max_tokens=self.max_tokens)
        def _weekly_io_analysis_simple(
                sys_message: str,
                meals_str: str,
                targets_str: str,
                restrictions_str: str
        ) -> str:
            sys_message += f"You must absolutely respond in this format with no exceptions. {NutritionFeedback.model_json_schema()}"
            return [
                ell.system(sys_message),
                ell.user([meals_str, targets_str, restrictions_str])
            ]

        sys_message = """ 
        You are a nutritionist providing feedback on a week's nutrition logs. Analyze the 
        user's nutritional intake versus their targets, including macro and micronutrient balance,
        meal timing, and portion sizes.
        
        Identify both positive patterns and areas for improvement. 
        When discussing concerns, focus on repeated patterns that significantly impact their 
        nutritional goals. For example, if frequent fried food consumption is causing them to 
        exceed fat targets, point this out specifically.

        Prioritize the 2-3 most important changes that would help them reach their goals. When 
        suggesting modifications, recommend realistic substitutions that maintain similar taste and 
        texture profiles. For instance, if they enjoy crunchy snacks but are exceeding sodium targets,
        suggest specific lower-sodium alternatives they might enjoy.

        Provide practical, actionable suggestions that respect their provided dietary restrictions. 
        Consider their current food preferences when making recommendations - the goal is to refine 
        their existing habits rather than completely overhaul their diet.

        Write your response in plain text paragraphs without bullets or special formatting, address 
        the user directly as their nutritionist.
        """ #TODO: this can be parsed in as an arg
        
        current_time = datetime.now().time()
        meals_str = f"As of {current_time} are the meals the user has logged today:\n"
        for i, (day, meals) in enumerate(meals.items()):
                meals_str += f"On {day} the user has logged the following meals:\n"
                for meal in meals:
                    meals_str += f"""Meal {meal.title} - {meal.calories} calories, 
                    {meal.macronutrients.protein}g protein, {meal.macronutrients.carbohydrates.total}g carbs, 
                    {meal.macronutrients.fat.total}g fat\n
                    Micros: {meal.micronutrients.vitamin_a}IU vit A, {meal.micronutrients.vitamin_c}mg vit C, 
                    {meal.micronutrients.iron}mg iron, {meal.micronutrients.calcium}mg calcium, 
                    {meal.micronutrients.sodium}mg sodium, {meal.micronutrients.potassium}mg potassium\n"""
            
                targets_str = f"""
                    The user's daily targets for {day} are: Calories: {target[i]["calories"]},
                    Protein: {target[i]["protein"]}g, Carbohydrates: {target[i]["carbs"]}g, Fat: {target[i]["fat"]}g
                    Micronutrient targets: Vitamin A: {target[i]["vitamin_a"]}IU, Vitamin C: {target[i]["vitamin_c"]}mg,
                    Iron: {target[i]["iron"]}mg, Calcium: {target[i]["calcium"]}mg,
                    Sodium: {target[i]["sodium"]}mg, Potassium: {target[i]["potassium"]}mg
                """
       
        restrictions_str = f"The user's dietary restrictions are: {restrictions}"
        
        if self.model in STRUCTURED_MODELS:
            analysis = _weekly_io_analysis_pydantic(
                sys_message, meals_str, targets_str, restrictions_str
            ).content[0].parsed
        else:
            analysis = _weekly_io_analysis_simple(sys_message, meals_str, targets_str, restrictions_str)
            analysis = NutritionFeedback.model_validate_json(analysis)
        
        return analysis
    
    def nutrient_analysis(
            self,
            nutrient: str,
            unit: str,
            intake: float,
            target: float,
            multiple_days: bool = False
        ) -> str:
        """Analyze if user is over/under their target for a specific nutrient.
        
        Args:
            nutrient: The nutrient being analyzed (e.g. 'vitamin_a', 'vitamin_c', 'iron', 'calcium', 'sodium', 'potassium')
            intake: The user's intake for this nutrient
            target: The target amount for this nutrient
        
        Returns:
            A string indicating if user is over/under target and by how much
        """
        nutrient = nutrient.lower()
        
        difference = intake - target
        if nutrient == "calories":
            nutrient = "caloric"
        elif nutrient == "carbohydrate":
            nutrient = "carbohydrates"

        if multiple_days:
            prefix = "You have been"
        else:
            prefix = "You are currently"
        
        if difference > 0:
            analysis = f"{abs(difference):.1f}{unit} over your {nutrient} target"
        elif difference < 0:
            analysis = f"{abs(difference):.1f}{unit} under your {nutrient} target"
        else:
            analysis = f"in line with your {nutrient} target"
        
        if multiple_days:
            analysis = f"{analysis} on average"
        
        return f"{prefix} {analysis}"
            