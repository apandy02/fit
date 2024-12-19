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
    
    def daily_io_analysis(self, meals: list[MealBreakdown], target: dict[str, float]) -> str:
        """
        Analyzes the user's daily intake and target and produces an overview with feedback.

        Args:
            meals: The user's meals for the day.
            target: The user's target for the day.
        """
        
        if len(meals) == 0:
            return "No meals logged for today, please log your meals and try again."

        @ell.simple(model=self.model)
        def _daily_io_analysis(meals: list[MealBreakdown], target: dict[str, float]) -> str:
            """
            Given the user's intake and target, provide a summary of the user's intake for the day. 
            
            If the user is over their target, highlight for them specific meals they ate that led to this. If the 
            meal is objectively bad, for example if they have a carbohydrate target of 50g and they ate 60g 
            alone in this one meal, recommend that they avoid that meal in the future. If any meal is driving 
            that number up but is not objectively bad, recommend to them adjusted portions. Do this for any 
            future. If any meal is driving that number up but is not objectively bad, recommend to them 
            adjusted portions. Do this for any and all macros, calories, and meals.

            If the user is under their target, let them know what they could have added to their diet to 
            get to their target. Make sure that the suggestions are not too extreme, and that they are 
            realistic. Use their prior intake to make suggestions. For example, if they seem to be eating 
            a lot of one cuisine, recommend things that aren't radically different.
            
            ***Respond in plain text (paragraph format). do not use bullet points. you may bold certain phrases to highlight using **
            . bold things that you think most require the users attention. for example "you are currently 10g under 
            your protein target"***
            """
            meals_str = "Here are the meals you've had today:\n"
            print(target)
            for i, meal in enumerate(meals, 1):
                meals_str += f"Meal {i}: {meal.summary} - {meal.calories} calories, "
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
            
            return f"{meals_str}\n{targets_str}"
        
        return _daily_io_analysis(meals, target)
    
    def macro_analysis(self, macro: str, intake: float, target: float) -> str:
        """Analyze if user is over/under their target for a specific macro.
        
        Args:
            macro: The macro being analyzed (e.g. 'protein', 'carbs', 'fat')
            intake: The user's intake for this macro
            target: The target amount for this macro
        
        Returns:
            A string indicating if user is over/under target and by how much
        """
        prefix = "Based on the information logged so far, "
        difference = intake - target
        if difference > 0:
            return f"{prefix}you are currently {abs(difference):.1f}g over your {macro} target"
        elif difference < 0:
            return f"{prefix}you are currently {abs(difference):.1f}g under your {macro} target"
        else:
            return f"{prefix}you are currently in line with your {macro} target"
            