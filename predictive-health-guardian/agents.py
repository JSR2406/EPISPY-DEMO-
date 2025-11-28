import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
import joblib

# --- ML Model Manager ---
class DiseaseRiskModels:
    def __init__(self):
        self.models = {}
        self.diseases = ['diabetes', 'heart_disease', 'hypertension', 'cancer', 'rare_disease']
        self.is_trained = False

    def train_models(self, data_path='synthetic_health_data.csv'):
        try:
            df = pd.read_csv(data_path)
        except FileNotFoundError:
            print("Data file not found. Please run data.py first.")
            return

        X = df[['age', 'bmi', 'bp_systolic']]
        # Simple encoding for symptoms if we were using them directly in ML, 
        # but for this MVP we'll stick to vitals + simple symptom count heuristic for the ML baseline
        # to keep it robust and simple for the "RandomForest" part.
        # The prompt says "RandomForest trained on 2000 synthetic...".
        # We'll use the generated columns as targets.
        
        for disease in self.diseases:
            y = df[f'has_{disease}']
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X, y)
            self.models[disease] = clf
        
        self.is_trained = True
        print("ML Models trained successfully.")

    def predict_risks(self, age, bmi, bp_systolic, symptoms_text):
        if not self.is_trained:
            self.train_models()
        
        # Base ML prediction from vitals
        input_data = pd.DataFrame([[age, bmi, bp_systolic]], columns=['age', 'bmi', 'bp_systolic'])
        risks = {}
        
        for disease in self.diseases:
            prob = self.models[disease].predict_proba(input_data)[0][1]
            risks[disease.replace('_', ' ').title()] = round(prob * 100, 1)
            
        # Heuristic adjustments based on symptoms (Hybrid approach for better demo accuracy)
        # This mimics what the "SymptomParser" agent would feed into a more complex model
        symptoms_lower = symptoms_text.lower()
        if 'thirst' in symptoms_lower or 'urination' in symptoms_lower:
            risks['Diabetes'] = min(99.9, risks.get('Diabetes', 0) + 30)
        if 'chest' in symptoms_lower or 'breath' in symptoms_lower:
            risks['Heart Disease'] = min(99.9, risks.get('Heart Disease', 0) + 30)
        if 'headache' in symptoms_lower and 'vision' in symptoms_lower:
            risks['Hypertension'] = min(99.9, risks.get('Hypertension', 0) + 20)
            
        return risks

# --- CrewAI Agents ---

class HealthAgents:
    def __init__(self):
        self.ml_models = DiseaseRiskModels()
        # Train on init for the hackathon demo speed
        if os.path.exists('synthetic_health_data.csv'):
            self.ml_models.train_models()
        
        # If no OpenAI key, we might fallback to just ML, but we define agents structure anyway
        # Assuming environment variables are set for CrewAI (OPENAI_API_KEY, etc.)
        
    def get_analysis(self, age, bmi, bp_systolic, symptoms):
        # 1. ML Prediction (Fast, Reliable)
        ml_risks = self.ml_models.predict_risks(age, bmi, bp_systolic, symptoms)
        
        # 2. Agentic Workflow (Rich, Explanatory)
        # For the hackathon demo, if we don't have an LLM key, we return ML results + template text.
        # If we do, we run the crew.
        
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "risks": ml_risks,
                "recommendations": self._generate_fallback_recommendations(ml_risks),
                "analysis": "LLM API Key not found. Using ML models only."
            }

        # Define Agents
        symptom_parser = Agent(
            role='Symptom Parser',
            goal='Extract key medical symptoms from patient text',
            backstory='Expert medical scribe capable of identifying clinical signs from natural language.',
            verbose=True,
            allow_delegation=False
        )

        risk_predictor = Agent(
            role='Risk Predictor',
            goal='Assess disease risk based on vitals and parsed symptoms',
            backstory='Senior Diagnostician using statistical models and clinical guidelines.',
            verbose=True,
            allow_delegation=False
        )

        action_planner = Agent(
            role='Action Planner',
            goal='Create a prioritized health action plan',
            backstory='Wellness consultant focused on preventative care and lifestyle interventions.',
            verbose=True,
            allow_delegation=False
        )

        # Define Tasks
        task1 = Task(
            description=f"Analyze these symptoms: '{symptoms}'. List the key clinical terms.",
            agent=symptom_parser,
            expected_output="List of clinical symptoms"
        )

        task2 = Task(
            description=f"Patient Vitals: Age {age}, BMI {bmi}, BP {bp_systolic}. Symptoms: {{task1_output}}. "
                        f"ML Risk Estimates: {ml_risks}. "
                        "Provide a risk assessment summary confirming or refining the ML estimates.",
            agent=risk_predictor,
            expected_output="Risk assessment summary"
        )

        task3 = Task(
            description="Based on the risk assessment, create a 3-step prioritized action plan for the patient.",
            agent=action_planner,
            expected_output="3-step action plan"
        )

        crew = Crew(
            agents=[symptom_parser, risk_predictor, action_planner],
            tasks=[task1, task2, task3],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        
        return {
            "risks": ml_risks,
            "recommendations": str(result), # The final output is the action plan
            "analysis": "Agents successfully analyzed the patient."
        }

    def _generate_fallback_recommendations(self, risks):
        # Simple rule-based fallback if LLM is down
        top_risk = max(risks, key=risks.get)
        if top_risk == 'Diabetes':
            return "1. Schedule HbA1c test. 2. Reduce sugar intake. 3. Increase daily walking."
        elif top_risk == 'Heart Disease':
            return "1. Consult cardiologist immediately. 2. Monitor BP daily. 3. Low sodium diet."
        elif top_risk == 'Hypertension':
            return "1. Regular BP monitoring. 2. Reduce stress. 3. Limit alcohol and caffeine."
        else:
            return "1. Annual checkup recommended. 2. Maintain balanced diet. 3. Regular exercise."

if __name__ == "__main__":
    # Test
    agents = HealthAgents()
    print(agents.get_analysis(45, 28, 135, "feeling thirsty and tired"))
