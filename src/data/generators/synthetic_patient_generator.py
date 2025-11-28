import pandas as pd
import numpy as np
from faker import Faker
import random
import os

def generate_synthetic_patient_data(num_patients=2000, output_path='data/synthetic_health_data.csv'):
    """
    Generate 2000 patients with CORRELATED risks (age↑=diabetes↑, BP↑=heart↑)
    Output: synthetic_health_data.csv with 9 columns
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fake = Faker()
    data = []

    for _ in range(num_patients):
        # Base demographics
        age = random.randint(20, 90)
        
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
        symptoms_str = " ".join(patient_symptoms) if patient_symptoms else "None"

        # Calculate Ground Truth Risks (0-95 scale)
        
        # Diabetes Risk
        # bmi > 30 = diabetes_risk +25%
        diabetes_risk = 10 # Base
        if age > 45: diabetes_risk += 20
        if bmi > 25: diabetes_risk += 15
        if bmi > 30: diabetes_risk += 25
        if 'frequent_urination' in patient_symptoms: diabetes_risk += 15
        if 'excessive_thirst' in patient_symptoms: diabetes_risk += 10
        diabetes_risk = min(95, diabetes_risk + random.randint(-5, 5))

        # Heart Disease Risk
        heart_risk = 10 # Base
        if age > 50: heart_risk += 20
        if bp_systolic > 140: heart_risk += 30 # bp_systolic > 140 = hypertension/heart risk +30%
        if 'chest_pain' in patient_symptoms: heart_risk += 25
        if 'shortness_of_breath' in patient_symptoms: heart_risk += 10
        heart_risk = min(95, heart_risk + random.randint(-5, 5))

        # Hypertension Risk
        # bp_systolic > 140 = hypertension_risk +30%
        hypertension_risk = 10 # Base
        if bp_systolic > 130: hypertension_risk += 20
        if bp_systolic > 140: hypertension_risk += 30
        if age > 60: hypertension_risk += 15
        if 'headache' in patient_symptoms: hypertension_risk += 10
        hypertension_risk = min(95, hypertension_risk + random.randint(-5, 5))
        
        # Cancer Risk (Simplified)
        cancer_risk = 5 # Base
        if age > 60: cancer_risk += 20
        if 'lump_in_breast' in patient_symptoms: cancer_risk += 60
        if 'persistent_cough' in patient_symptoms: cancer_risk += 20
        if 'unexplained_weight_loss' in patient_symptoms: cancer_risk += 20
        cancer_risk = min(95, cancer_risk + random.randint(-5, 5))
        
        # Rare Disease Risk (Simplified)
        rare_disease_risk = 2 # Base
        if 'muscle_weakness' in patient_symptoms and 'skin_rash' in patient_symptoms: rare_disease_risk += 80
        rare_disease_risk = min(95, rare_disease_risk + random.randint(-2, 5))

        data.append({
            'age': age,
            'bmi': bmi,
            'bp_systolic': bp_systolic,
            'symptoms': symptoms_str,
            'diabetes_risk': diabetes_risk,
            'heart_risk': heart_risk,
            'hypertension_risk': hypertension_risk,
            'cancer_risk': cancer_risk,
            'rare_disease_risk': rare_disease_risk
        })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Generated {num_patients} patient records in {output_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_patient_data()
