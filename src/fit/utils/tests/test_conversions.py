import unittest
from fit.utils.conversions import kj_to_kcal

class TestConversions(unittest.TestCase):
    def test_kj_to_kcal(self):
        self.assertAlmostEqual(kj_to_kcal(4.184), 1.0)
        self.assertEqual(kj_to_kcal(0), 0)
        self.assertAlmostEqual(kj_to_kcal(418.4), 100.0)    
        self.assertAlmostEqual(kj_to_kcal(-4.184), -1.0)

