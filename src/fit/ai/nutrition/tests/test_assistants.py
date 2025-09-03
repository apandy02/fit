import unittest

from fit.ai.nutrition.assistants import nutrient_analysis


class TestNutrientAnalysis(unittest.TestCase):
    def test_nutrient_analysis(self):
        # Test over target
        self.assertEqual(
            nutrient_analysis("protein", "g", 150, 100),
            "You are currently 50.0g over your protein target"
        )
        
        self.assertEqual(
            nutrient_analysis("vitamin_c", "mg", 50, 90),
            "You are currently 40.0mg under your vitamin_c target"
        )
        
        self.assertEqual(
            nutrient_analysis("iron", "mg", 18, 18),
            "You are currently in line with your iron target"
        )

        self.assertEqual(
            nutrient_analysis("calories", "kcal", 2200, 2000),
            "You are currently 200.0kcal over your caloric target"
        )
        
        self.assertEqual(
            nutrient_analysis("carbohydrates", "g", 180, 200),
            "You are currently 20.0g under your carbohydrate target"
        )
        
        self.assertEqual(
            nutrient_analysis("protein", "g", 150, 100, multiple_days=True),
            "You have been 50.0g over your protein target on average"
        )
