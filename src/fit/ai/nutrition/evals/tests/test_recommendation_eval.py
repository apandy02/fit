import unittest

from fit.ai.nutrition.evals.recommendation_eval import (calculate_final_totals,
                                                        calculate_penalty,
                                                        calculate_target_score,
                                                        prepare_eval_data)


class TestRecommendationEval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eval_data = prepare_eval_data()[0]
        cls.current = cls.eval_data["consumption"]
        cls.targets = cls.eval_data["targets"]
        cls.target_nutrient = cls.eval_data["target_nutrient"]

    def test_calculate_target_score(self):
        final_totals = {"protein": 116}
        self.assertEqual(calculate_target_score(final_totals, "protein", 116), 1.0)

        final_totals = {"protein": 92.8}
        self.assertAlmostEqual(
            calculate_target_score(final_totals, "protein", 116), 0.8
        )

        final_totals = {"protein": 139.2}
        self.assertAlmostEqual(
            calculate_target_score(final_totals, "protein", 116), 0.8
        )

    def test_calculate_penalty(self):
        final_totals = {
            "protein": self.targets["protein"] * 1.2,
            "carbohydrates": self.targets["carbohydrates"],
            "fat": self.targets["fat"] * 1.5,
            "vitamin_a": self.targets["vitamin_a"],
            "vitamin_c": self.targets["vitamin_c"],
            "vitamin_d": self.targets["vitamin_d"],
            "calcium": self.targets["calcium"],
            "iron": self.targets["iron"],
            "potassium": self.targets["potassium"],
            "sodium": self.targets["sodium"],
        }

        self.assertAlmostEqual(calculate_penalty(final_totals, self.targets), -0.7)

        final_totals = {k: v * 0.9 for k, v in self.targets.items()}
        self.assertEqual(calculate_penalty(final_totals, self.targets), 0.0)

        final_totals = {k: v * 3 for k, v in self.targets.items()}
        self.assertEqual(calculate_penalty(final_totals, self.targets), -1.0)

    def test_calculate_final_totals(self):
        recommendation_averages = {
            "calories": 500,
            "protein": 25.0,
            "carbohydrates": 50.0,
            "fat": 15.0,
            "vitamin_a": 250,
            "vitamin_c": 30,
            "vitamin_d": 5,
            "calcium": 400,
            "iron": 4,
            "potassium": 1000,
            "sodium": 750,
        }

        final_totals = calculate_final_totals(self.current, recommendation_averages)

        self.assertEqual(
            final_totals["calories"],
            self.current.calories + recommendation_averages["calories"],
        )
        self.assertEqual(
            final_totals["protein"],
            self.current.macronutrients.protein + recommendation_averages["protein"],
        )
        self.assertEqual(
            final_totals["carbohydrates"],
            self.current.macronutrients.carbohydrates.total
            + recommendation_averages["carbohydrates"],
        )
        self.assertEqual(
            final_totals["fat"],
            self.current.macronutrients.fat.total + recommendation_averages["fat"],
        )

        for nutrient in [
            "vitamin_a",
            "vitamin_c",
            "vitamin_d",
            "calcium",
            "iron",
            "potassium",
            "sodium",
        ]:
            self.assertEqual(
                final_totals[nutrient],
                getattr(self.current.micronutrients, nutrient)
                + recommendation_averages[nutrient],
            )
