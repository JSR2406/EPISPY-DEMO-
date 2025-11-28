import pandas as pd
import numpy as np
from faker import Faker
import random

def generate_synthetic_data(num_patients=2000):
    """
    Generate 2000 patients with CORRELATED risks (age↑=diabetes↑, BP↑=heart↑)
    Output: synthetic_health_data.csv with 9 columns
    """
    fake = Faker()
    data = []

    for _ in range(num_patients):
        # Base demographics
        age = random.randint(20, 90)
        gender = random.choice(['Male', 'Female'])
        
        # Correlated vitals based on age
        # Older people tend to have higher BP and BMI
        base_systolic = 110 + (age - 20) * 0.5
        bp_systolic = int(np.random.normal(base_systolic, 15))
        
        base_bmi = 22 + (age - 20) * 0.1
        bmi = round(np.random.normal(base_bmi, 4), 1)
        
        # Symptoms (Randomly assigned but weighted by health status)
        possible_symptoms = [
            'frequent_urination', 'excessive_thirst', 'unexplained_weight_loss', # Diabetes
            'chest_pain', 'shortness_of_breath', 'palpitations', # Heart
            'headache', 'blurred_vision', 'dizziness', # Hypertension
            'fatigue', 'lump_in_breast', 'persistent_cough', # Cancer
            'muscle_weakness', 'joint_pain', 'skin_rash' # Rare/General
        ]
        
        # Risk factors increase symptom count
        num_symptoms = 0
        if age > 50 or bmi > 30 or bp_systolic > 140:
            num_symptoms = random.randint(1, 4)
        
        patient_symptoms = random.sample(possible_symptoms, num_symptoms) if num_symptoms > 0 else []
        symptoms_str = ", ".join(patient_symptoms) if patient_symptoms else "None"

        # Calculate Ground Truth Risks (for training)
        # Simple heuristic rules to label data for the ML model to learn
        
        # Diabetes Risk
        diabetes_risk = 0
        if age > 45: diabetes_risk += 1
        if bmi > 25: diabetes_risk += 1
        if bmi > 30: diabetes_risk += 1
        if 'frequent_urination' in patient_symptoms: diabetes_risk += 2
        if 'excessive_thirst' in patient_symptoms: diabetes_risk += 2
        has_diabetes = 1 if diabetes_risk >= 3 else 0

        # Heart Disease Risk
        heart_risk = 0
        if age > 50: heart_risk += 1
        if bp_systolic > 140: heart_risk += 2
        if 'chest_pain' in patient_symptoms: heart_risk += 3
        if 'shortness_of_breath' in patient_symptoms: heart_risk += 1
        has_heart_disease = 1 if heart_risk >= 3 else 0

        # Hypertension Risk
        hypertension_risk = 0
        if bp_systolic > 130: hypertension_risk += 1
        if bp_systolic > 140: hypertension_risk += 2
        if age > 60: hypertension_risk += 1
        if 'headache' in patient_symptoms: hypertension_risk += 1
        has_hypertension = 1 if hypertension_risk >= 2 else 0
        
        # Cancer Risk (Simplified)
        cancer_risk = 0
        if age > 60: cancer_risk += 1
        if 'lump_in_breast' in patient_symptoms: cancer_risk += 5
        if 'persistent_cough' in patient_symptoms: cancer_risk += 2
        if 'unexplained_weight_loss' in patient_symptoms: cancer_risk += 2
        has_cancer = 1 if cancer_risk >= 3 else 0
        
        # Rare Disease Risk (Simplified)
        rare_risk = 0
        if 'muscle_weakness' in patient_symptoms and 'skin_rash' in patient_symptoms: rare_risk += 3
        has_rare_disease = 1 if rare_risk >= 3 else 0

        data.append({
            'age': age,
            'gender': gender,
            'bmi': bmi,
            'bp_systolic': bp_systolic,
            'symptoms': symptoms_str,
            'has_diabetes': has_diabetes,
            'has_heart_disease': has_heart_disease,
            'has_hypertension': has_hypertension,
            'has_cancer': has_cancer,
            'has_rare_disease': has_rare_disease
        })

    df = pd.DataFrame(data)
    df.to_csv('synthetic_health_data.csv', index=False)
    print(f"Generated {num_patients} patient records in synthetic_health_data.csv")
    return df

if __name__ == "__main__":
    generate_synthetic_data()
