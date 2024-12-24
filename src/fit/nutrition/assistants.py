from datetime import datetime

import ell

from fit.nutrition.data import Goals, MealBreakdown


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
    
    def image_macros(self, image: str) -> MealBreakdown:
        """Returns the macro nutrients in grams and kilocalories for food described in an image.
        Args:
            image: The image to get the macro nutrients for.
        """
        @ell.complex(model=self.model, response_format=MealBreakdown)
        def _image_macros(image: str) -> MealBreakdown:
            """given an image of what the user ate, return the macro nutrients in grams.
            If the image is not food, return 0 for all macros.
            """
            return image
        
        message = _image_macros(image)
        return message.content[0].parsed


class Nutritionist:
    """A class that uses LLMs recommend foods. Based on the user's caloric burn and macro goals."""
    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        """
        Args:
            model: The LLM to use.
        """
        self.model = model
    
    def make_recommendations(
            self, caloric_burn: float, goal: Goals, prior_intake: MealBreakdown
        ) -> str:
        """Makes recommendations for foods based on the user's caloric burn and macro goals.
        Args:
            caloric_burn: The user's caloric burn for the day.
            goal: The user's weight goals.
            prior_intake: The user's prior intake for the day.
        """
        @ell.simple(model=self.model)
        def _make_recommendations(
                caloric_burn: float, goal: Goals, prior_intake: MealBreakdown
            ) -> str:
            """given the user's caloric burn and weight goals, provide the user with 3 meal options.
            Ensure that your response is concise and easy to understand.
            """
            user_input = f"""
            The user's caloric burn for the day is {caloric_burn} calories. 
            The user's goal is to {goal.value}. 
            The user's prior intake for the day is {prior_intake.protein}g protein, 
            {prior_intake.carbs}g carbs, and {prior_intake.fat}g fat.
            """
            return user_input
        
        return _make_recommendations(caloric_burn, goal, prior_intake)
    
    def daily_io_analysis(self, meals: list[MealBreakdown], target: dict[str, float], restrictions: list[str]) -> str:
        """
        Analyzes the user's daily intake and target and produces an overview with feedback.

        Args:
            meals: The user's meals for the day.
            target: The user's target for the day.
        """
        if len(meals) == 0:
            return "No meals logged for today, please log your meals and try again."

        @ell.simple(model=self.model)
        def _daily_io_analysis(meals: list[MealBreakdown], target: dict[str, float], restrictions: list[str]) -> str:
            """Analyze the user's daily nutritional intake versus their targets and provide a detailed 
            assessment in plain text format. Start with an overview comparing total intake to goals. 
            Then evaluate each meal's contribution to any excess - flag meals that significantly exceed 
            targets (e.g., >100% of a macro target in one meal) as problematic and suggest alternatives. 
            if the current time of day is before 8PM and they're over their caloric target, suggest 
            a workout that get them closer to a target range.
            
            For meals contributing to excess but not extreme, recommend portion adjustments. 
            For under-target scenarios, suggest realistic additions based on their evident food preferences 
            and eating patterns.

            You will be provided with the user's dietary restrictions, make sure not to recommend any foods
            that are restricted.

            Break the analysis into four sections:
            An untitled general overview
            <b>Macronutrients</b>
            <b>Micronutrients</b>
            <b>Suggestions</b>

            Format as plain text paragraphs without bullets, markdown, or special formatting , you are 
            speaking to the user directly as their nutritionist. 
            (except section headers in <b> tags). Each section should flow naturally in paragraph form."""
            current_time = datetime.now().time()
            meals_str = f"As of {current_time} are the meals the user has logged today:\n"
            
            for i, meal in enumerate(meals, 1):
                meals_str += f"Meal {meal.summary} - {meal.calories} calories, "
                meals_str += f"{meal.protein}g protein, {meal.carbs}g carbs, {meal.fat}g fat\n"
                meals_str += f"Micros: {meal.vitamin_a}IU vit A, {meal.vitamin_c}mg vit C, "
                meals_str += f"{meal.iron}mg iron, {meal.calcium}mg calcium, "
                meals_str += f"{meal.sodium}mg sodium, {meal.potassium}mg potassium\n"
            
            targets_str = f"""
                The user's daily targets are: Calories: {target["calories"]}, Protein: {target["protein"]}g,
                Carbohydrates: {target["carbs"]}g, Fat: {target["fat"]}g
                Micronutrient targets: Vitamin A: {target["vitamin_a"]}IU, Vitamin C: {target["vitamin_c"]}mg,
                Iron: {target["iron"]}mg, Calcium: {target["calcium"]}mg,
                Sodium: {target["sodium"]}mg, Potassium: {target["potassium"]}mg
            """
            restrictions_str = f"The user's dietary restrictions are: {restrictions}"

            return f"{meals_str}\n{targets_str}\n{restrictions_str}"
        
        return _daily_io_analysis(meals, target, restrictions)

    def weekly_io_analysis(self, meals: dict[datetime, list[MealBreakdown]], target: dict[str, float], restrictions: list[str]) -> str:
        """
        Analyzes the user's weekly intake and target and produces an overview with feedback.

        Args:
            meals: The user's meals for the week, stored per day.
            target: The user's target for the week, stored per day.
        """
        if len(meals) == 0:
            return "No meals logged for today, please log your meals and try again."

        @ell.simple(model=self.model)
        def _weekly_io_analysis(meals: dict[datetime, list[MealBreakdown]], target: dict[str, float], restrictions: list[str]) -> str:
            """ 
            Given the user's meals for the week, provide a detailed assessment of their nutritional 
            intake versus their targets.

            Highlight for them patterns. For example, if they are repeatedly eating fries and the fries is causing them to exceed their
            sodium target, point out that they ate fries too much. 

            Make for them suggestions for how to improve their progress towards their goals. You will be provided
            with the user's dietary restrictions, make sure not to recommend any foods that are restricted.

            Break the analysis into four sections:
            An untitled general overview
            <b>Macronutrients</b>
            <b>Micronutrients</b>
            <b>Suggestions</b>

            Format as plain text paragraphs without bullets, markdown, or special formatting , you are 
            speaking to the user directly as their nutritionist. 
            (except section headers in <b> tags). Each section should flow naturally in paragraph form."""
            current_time = datetime.now().time()
            meals_str = f"As of {current_time} are the meals the user has logged today:\n"
            
            for i, (day, meals) in enumerate(meals.items()):
                meals_str += f"On {day} the user has logged the following meals:\n"
                for meal in meals:
                    meals_str += f"Meal {meal.summary} - {meal.calories} calories, "
                    meals_str += f"{meal.protein}g protein, {meal.carbs}g carbs, {meal.fat}g fat\n"
                    meals_str += f"Micros: {meal.vitamin_a}IU vit A, {meal.vitamin_c}mg vit C, "
                    meals_str += f"{meal.iron}mg iron, {meal.calcium}mg calcium, "
                    meals_str += f"{meal.sodium}mg sodium, {meal.potassium}mg potassium\n"
            
                targets_str = f"""
                    The user's daily targets for {day} are: Calories: {target[i]["calories"]}, Protein: {target[i]["protein"]}g,
                    Carbohydrates: {target[i]["carbs"]}g, Fat: {target[i]["fat"]}g
                    Micronutrient targets: Vitamin A: {target[i]["vitamin_a"]}IU, Vitamin C: {target[i]["vitamin_c"]}mg,
                    Iron: {target[i]["iron"]}mg, Calcium: {target[i]["calcium"]}mg,
                    Sodium: {target[i]["sodium"]}mg, Potassium: {target[i]["potassium"]}mg
                """
            restrictions_str = f"The user's dietary restrictions are: {restrictions}"

            return f"{meals_str}\n{targets_str}\n{restrictions_str}"
        
        return _weekly_io_analysis(meals, target, restrictions)
    
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
        
        prefix = "Based on the information logged so far, "
        if multiple_days:
            prefix += "you have been"
        else:
            prefix += "you are currently"
        
        if difference > 0:
            analysis = f"{abs(difference):.1f}{unit} over your {nutrient} target"
        elif difference < 0:
            analysis = f"{abs(difference):.1f}{unit} under your {nutrient} target"
        else:
            analysis = f"in line with your {nutrient} target"
        
        if multiple_days:
            analysis = f"{analysis} on average"
        
        return f"{prefix} {analysis}"
            