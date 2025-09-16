import unittest

import fit.utils.conversions as conversions


class TestConversions(unittest.TestCase):
    def test_lbs_to_kg(self):
        self.assertAlmostEqual(conversions.lbs_to_kg(1), 0.453592)
        self.assertEqual(conversions.lbs_to_kg(0), 0)
        self.assertAlmostEqual(conversions.lbs_to_kg(2.20462), 1.0, places=5)
        self.assertAlmostEqual(conversions.lbs_to_kg(-1), -0.453592)

    def test_kg_to_lbs(self):
        self.assertAlmostEqual(conversions.kg_to_lbs(1), 2.20462)
        self.assertEqual(conversions.kg_to_lbs(0), 0)
        self.assertAlmostEqual(conversions.kg_to_lbs(0.453592), 1.0, places=5)
        self.assertAlmostEqual(conversions.kg_to_lbs(-1), -2.20462)

    def test_ml_to_oz(self):
        self.assertAlmostEqual(conversions.ml_to_oz(1), 0.033814)
        self.assertEqual(conversions.ml_to_oz(0), 0)
        self.assertAlmostEqual(conversions.ml_to_oz(29.5735), 1.0, places=5)
        self.assertAlmostEqual(conversions.ml_to_oz(-1), -0.033814)

    def test_oz_to_ml(self):
        self.assertAlmostEqual(conversions.oz_to_ml(1), 29.5735)
        self.assertEqual(conversions.oz_to_ml(0), 0)
        self.assertAlmostEqual(conversions.oz_to_ml(0.033814), 1.0, places=5)
        self.assertAlmostEqual(conversions.oz_to_ml(-1), -29.5735)
