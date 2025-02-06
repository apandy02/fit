import unittest

from fit.nutrition.data_models import WeightGoal
from fit.nutrition.targets import (MICRO_GOALS, calculate_caloric_target,
                                   calculate_carb_target, calculate_fat_target,
                                   calculate_macro_targets,
                                   calculate_protein_target)


class TestTargets(unittest.TestCase):
    def test_calculate_caloric_target(self):
        self.assertEqual(calculate_caloric_target(2000, WeightGoal.GAIN), 2200)
        self.assertEqual(calculate_caloric_target(2000, WeightGoal.LOSE), 1800)
        self.assertEqual(calculate_caloric_target(2000, WeightGoal.MAINTAIN), 2000)
        self.assertEqual(calculate_caloric_target(0, WeightGoal.MAINTAIN), 0)

    def test_calculate_protein_target(self):
        self.assertEqual(calculate_protein_target(2000), 150)
        self.assertEqual(calculate_protein_target(0), 0)
        self.assertEqual(calculate_protein_target(4000), 300)

    def test_calculate_fat_target(self):
        self.assertAlmostEqual(calculate_fat_target(2000), 66.67, places=2)
        self.assertEqual(calculate_fat_target(0), 0)
        self.assertAlmostEqual(calculate_fat_target(4000), 133.33, places=2)

    def test_calculate_carb_target(self):
        self.assertEqual(calculate_carb_target(2000), 200)
        self.assertEqual(calculate_carb_target(0), 0)
        self.assertEqual(calculate_carb_target(4000), 400)

    def test_calculate_macro_targets(self):
        result = calculate_macro_targets(2000, WeightGoal.GAIN)
        self.assertEqual(result["calories"], 2200)
        self.assertEqual(result["protein"], 165)
        self.assertEqual(result["fat"], 73)
        self.assertEqual(result["carbohydrates"], 220)
        
        result = calculate_macro_targets(2000, WeightGoal.LOSE)
        self.assertEqual(result["calories"], 1800)
        self.assertEqual(result["protein"], 135)
        self.assertEqual(result["fat"], 60)
        self.assertEqual(result["carbohydrates"], 180)
        
        result = calculate_macro_targets(2000, WeightGoal.MAINTAIN)
        self.assertEqual(result["calories"], 2000)
        self.assertEqual(result["protein"], 150)
        self.assertEqual(result["fat"], 67)
        self.assertEqual(result["carbohydrates"], 200)

    def test_micro_goals(self):
        self.assertIn("male", MICRO_GOALS)
        self.assertIn("female", MICRO_GOALS)
        
        required_micros = {"vitamin_a", "vitamin_c", "vitamin_d", "calcium", "iron", "potassium", "sodium"}
        for micro in required_micros:
            self.assertIn(micro, MICRO_GOALS["male"])
            self.assertIn(micro, MICRO_GOALS["female"])
        
        self.assertEqual(MICRO_GOALS["male"]["vitamin_c"], 90)
        self.assertEqual(MICRO_GOALS["female"]["vitamin_c"], 75)
