import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from crewai import Agent, Task, Crew, Process
from src.utils.logger import api_logger
from src.integrations.medical_knowledge import MedicalKnowledgeBase
import google.generativeai as genai
import json

# --- ML Model Manager ---
class DiseaseRiskModels:
    def __init__(self, data_path='data/synthetic_health_data.csv'):
        self.models = {}
        self.diseases = ['diabetes', 'heart', 'hypertension', 'cancer', 'rare_disease']
        self.is_trained = False
        self.data_path = data_path

    def train_models(self):
        if not os.path.exists(self.data_path):
            api_logger.info(f"Data file not found at {self.data_path}. Generating new data...")
            from src.data.generators.synthetic_patient_generator import generate_synthetic_patient_data

            generate_synthetic_patient_data(output_path=self.data_path)

        try:
            df = pd.read_csv(self.data_path)
        except Exception as e:
            api_logger.error(f"Error reading data file: {e}")
            return

        X = df[['age', 'bmi', 'bp_systolic']]
        
        for disease in self.diseases:
            # Target columns are named like 'diabetes_risk', 'heart_risk'
            target_col = f'{disease}_risk'
            if target_col not in df.columns:
                api_logger.warning(f"Target column {target_col} not found in data.")
                continue
                
            y = df[target_col]
            # Using Regressor as we are predicting a risk score 0-95
            clf = RandomForestRegressor(n_estimators=100, random_state=42)
            clf.fit(X, y)
            self.models[disease] = clf
        
        self.is_trained = True
        api_logger.info("ML Models trained successfully.")

    def predict_risks(self, age, bmi, bp_systolic, symptoms_text):
        if not self.is_trained:
            self.train_models()
        
        # Base ML prediction from vitals
        input_data = pd.DataFrame([[age, bmi, bp_systolic]], columns=['age', 'bmi', 'bp_systolic'])
        risks = {}
        
        disease_map = {
            'diabetes': 'Diabetes',
            'heart': 'Heart Disease',
            'hypertension': 'Hypertension',
            'cancer': 'Cancer',
            'rare_disease': 'Rare Disease'
        }

        for disease in self.diseases:
            if disease in self.models:
                score = self.models[disease].predict(input_data)[0]
                risks[disease_map[disease]] = round(score, 1)
            else:
                risks[disease_map[disease]] = 0.0
            
        # Heuristic adjustments based on symptoms (Hybrid approach)
        # This ensures the "SymptomParser" logic is reflected in the final numbers if ML didn't catch it from vitals alone
        symptoms_lower = symptoms_text.lower()
        if 'thirst' in symptoms_lower or 'urination' in symptoms_lower:
            risks['Diabetes'] = min(95.0, risks.get('Diabetes', 0) + 20)
        if 'chest' in symptoms_lower or 'breath' in symptoms_lower:
            risks['Heart Disease'] = min(95.0, risks.get('Heart Disease', 0) + 20)
        if 'headache' in symptoms_lower and 'vision' in symptoms_lower:
            risks['Hypertension'] = min(95.0, risks.get('Hypertension', 0) + 15)
        if 'lump' in symptoms_lower:
            risks['Cancer'] = min(95.0, risks.get('Cancer', 0) + 40)
            
        return risks

class HealthAgents:
    def __init__(self):
        # Ensure data path is correct relative to execution root
        self.ml_models = DiseaseRiskModels(data_path=os.path.join(os.getcwd(), 'data', 'synthetic_health_data.csv'))
        # Train on init
        self.ml_models.train_models()
        
        # Initialize RAG
        self.knowledge_base = MedicalKnowledgeBase()
        
        # Initialize Gemini
        self.gemini_available = False
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
                api_logger.info("Google Gemini Pro initialized successfully.")
            except Exception as e:
                api_logger.error(f"Failed to initialize Gemini: {e}")

    def run_agent_swarm(self, age, bmi, bp_systolic, symptoms, weather_context=None):
        # 1. ML Prediction (Fast, Reliable)
        ml_risks = self.ml_models.predict_risks(age, bmi, bp_systolic, symptoms)
        
        # 2. RAG Retrieval
        rag_context = []
        if self.knowledge_base.is_ready:
            # Search for guidelines related to symptoms and top risk
            top_risk = max(ml_risks, key=ml_risks.get)
            query = f"{top_risk} management guidelines {symptoms}"
            rag_context = self.knowledge_base.search(query)
        
        # 3. Advanced Reasoning (Gemini or Fallback)
        if self.gemini_available:
            return self._run_gemini_analysis(age, bmi, bp_systolic, symptoms, ml_risks, weather_context, rag_context)
        else:
            return self._run_fallback_analysis(ml_risks, symptoms, weather_context, rag_context)

    def _run_gemini_analysis(self, age, bmi, bp, symptoms, ml_risks, weather_context=None, rag_context=None):
        try:
            weather_str = f"Weather Context: {weather_context}" if weather_context else "Weather Context: Not available"
            rag_str = f"Medical Guidelines: {rag_context}" if rag_context else "Medical Guidelines: Standard protocols"
            
            prompt = f"""
            You are an expert Medical AI Assistant. Analyze this patient:
            - Age: {age}
            - BMI: {bmi}
            - Systolic BP: {bp}
            - Reported Symptoms: "{symptoms}"
            - Preliminary ML Risk Scores (0-100): {ml_risks}
            - {weather_str}
            - {rag_str}

            Task:
            1. Analyze the consistency between symptoms and vitals.
            2. Consider how the local weather might be affecting the patient's health.
            3. Use the provided Medical Guidelines to support your recommendations.
            4. Provide a medical interpretation of the ML scores.
            5. Generate 3 specific, prioritized recommendations citing the guidelines if relevant.
            6. Extract key clinical terms from the symptoms.

            Output strictly in valid JSON format:
            {{
                "analysis": "Brief clinical assessment including weather and guideline insights...",
                "recommendations": "1. ... 2. ... 3. ...",
                "processed_symptoms": "List of extracted clinical terms"
            }}
            """
            
            response = self.model.generate_content(prompt)
            cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
            ai_output = json.loads(cleaned_text)
            
            return {
                "risks": ml_risks,
                "recommendations": ai_output.get("recommendations", "Consult a doctor."),
                "processed_symptoms": ai_output.get("processed_symptoms", symptoms),
                "analysis": ai_output.get("analysis", "AI Analysis complete.")
            }
        except Exception as e:
            api_logger.error(f"Gemini analysis failed: {e}")
            return self._run_fallback_analysis(ml_risks, symptoms, weather_context, rag_context)

    def _run_fallback_analysis(self, risks, symptoms, weather_context=None, rag_context=None):
        # Fallback logic if Gemini is down or key is missing
        top_risk = max(risks, key=risks.get)
        rec_map = {
            'Diabetes': "1. Schedule HbA1c test. 2. Reduce sugar intake. 3. Increase daily walking.",
            'Heart Disease': "1. Consult cardiologist immediately. 2. Monitor BP daily. 3. Low sodium diet.",
            'Hypertension': "1. Regular BP monitoring. 2. Reduce stress. 3. Limit alcohol and caffeine.",
            'Cancer': "1. Schedule screening immediately. 2. Consult oncologist. 3. Detailed family history review.",
            'Rare Disease': "1. Genetic counseling. 2. Specialist referral. 3. Detailed symptom log."
        }
        
        weather_note = ""
        if weather_context and isinstance(weather_context, dict):
            if weather_context.get('temp', 20) > 30:
                weather_note = " Note: High temperatures detected. Stay hydrated."
            elif weather_context.get('temp', 20) < 5:
                weather_note = " Note: Low temperatures detected. Keep warm to reduce heart strain."
        
        rag_note = ""
        if rag_context:
            rag_note = f" (Guidelines found: {len(rag_context)})"

        return {
            "risks": risks,
            "recommendations": rec_map.get(top_risk, "1. Annual checkup. 2. Balanced diet. 3. Exercise.") + weather_note + rag_note,
            "processed_symptoms": f"Raw: {symptoms}",
            "analysis": "Standard ML Analysis (Gemini unavailable)" + weather_note
        }
