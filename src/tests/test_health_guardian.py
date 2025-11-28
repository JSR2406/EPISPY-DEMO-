import unittest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.agents.health_guardian_agent import HealthAgents
from src.data.generators.synthetic_patient_generator import generate_synthetic_patient_data

class TestHealthGuardian(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure data exists
        data_path = os.path.join(project_root, 'data', 'synthetic_health_data.csv')
        if not os.path.exists(data_path):
            generate_synthetic_patient_data(output_path=data_path)
        
        # Initialize agents
        cls.agents = HealthAgents()

    def test_ml_training(self):
        """Test if ML models are trained and available"""
        self.assertTrue(self.agents.ml_models.is_trained)
        self.assertEqual(len(self.agents.ml_models.models), 5)

    def test_prediction_structure(self):
        """Test if prediction returns correct structure"""
        result = self.agents.run_agent_swarm(30, 22, 120, "None")
        self.assertIn("risks", result)
        self.assertIn("recommendations", result)
        self.assertIn("processed_symptoms", result)
        
    def test_high_risk_logic(self):
        """Test if high risk inputs yield high risk scores"""
        # High BP + Chest Pain should trigger Heart Disease risk
        # Our logic adds 20 to risk if 'chest' is in symptoms.
        result = self.agents.run_agent_swarm(60, 30, 160, "chest pain")
        heart_risk = result['risks'].get('Heart Disease', 0)
        self.assertGreater(heart_risk, 30, "Heart Disease risk should be elevated for symptomatic patient")

    def test_low_risk_logic(self):
        """Test if healthy inputs yield low risk scores"""
        result = self.agents.run_agent_swarm(25, 22, 110, "None")
        diabetes_risk = result['risks'].get('Diabetes', 0)
        self.assertLess(diabetes_risk, 50, "Diabetes risk should be low for healthy patient")

if __name__ == '__main__':
    unittest.main()
