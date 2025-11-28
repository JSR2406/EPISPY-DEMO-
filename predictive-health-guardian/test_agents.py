import unittest
import os
from agents import HealthAgents
import pandas as pd

class TestHealthAgents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure data exists
        if not os.path.exists('synthetic_health_data.csv'):
            from data import generate_synthetic_data
            generate_synthetic_data()
        cls.agents = HealthAgents()

    def test_ml_training(self):
        """Test if ML models are trained and available"""
        self.assertTrue(self.agents.ml_models.is_trained)
        self.assertEqual(len(self.agents.ml_models.models), 5)

    def test_prediction_structure(self):
        """Test if prediction returns correct structure"""
        result = self.agents.get_analysis(30, 22, 120, "None")
        self.assertIn("risks", result)
        self.assertIn("recommendations", result)
        self.assertIn("analysis", result)
        
    def test_high_risk_logic(self):
        """Test if high risk inputs yield high risk scores"""
        # High BP + Chest Pain should trigger Heart Disease risk
        result = self.agents.get_analysis(60, 30, 160, "chest pain")
        heart_risk = result['risks'].get('Heart Disease', 0)
        self.assertGreater(heart_risk, 50, "Heart Disease risk should be high for symptomatic patient")

    def test_low_risk_logic(self):
        """Test if healthy inputs yield low risk scores"""
        result = self.agents.get_analysis(25, 22, 110, "None")
        diabetes_risk = result['risks'].get('Diabetes', 0)
        self.assertLess(diabetes_risk, 50, "Diabetes risk should be low for healthy patient")

if __name__ == '__main__':
    unittest.main()
