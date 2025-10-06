"""Generate synthetic patient data for testing."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
from faker import Faker
import uuid

fake = Faker()

class PatientDataGenerator:
    """Generate realistic anonymized patient data."""
    
    def __init__(self):
        self.symptoms_list = [
            "fever", "cough", "headache", "fatigue", "sore_throat",
            "runny_nose", "body_aches", "chills", "nausea", "vomiting",
            "diarrhea", "shortness_of_breath", "chest_pain", "dizziness"
        ]
        
        self.locations = [
            "Rural_Hospital_A", "Rural_Clinic_B", "Health_Center_C",
            "Mobile_Unit_D", "Community_Health_E", "Rural_Hospital_F"
        ]
        
        self.age_groups = ["0-5", "6-18", "19-35", "36-50", "51-65", "65+"]
    
    def generate_patient_record(self) -> Dict[str, Any]:
        """Generate a single anonymized patient record."""
        patient_id = str(uuid.uuid4())[:8]  # Short anonymous ID
        
        # Random symptoms (1-4 symptoms per patient)
        num_symptoms = random.randint(1, 4)
        symptoms = random.sample(self.symptoms_list, num_symptoms)
        
        # Generate timestamps (last 30 days)
        days_ago = random.randint(0, 30)
        visit_date = datetime.now() - timedelta(days=days_ago)
        
        return {
            "patient_id": patient_id,
            "visit_date": visit_date.isoformat(),
            "location": random.choice(self.locations),
            "age_group": random.choice(self.age_groups),
            "symptoms": symptoms,
            "severity_score": random.uniform(1, 10),  # 1=mild, 10=severe
            "latitude": round(random.uniform(18.0, 28.0), 4),  # India coordinates
            "longitude": round(random.uniform(68.0, 97.0), 4),
            "anonymized": True,
            "data_source": "synthetic_generator"
        }
    
    def generate_outbreak_scenario(
        self, 
        num_patients: int = 100,
        outbreak_probability: float = 0.3
    ) -> pd.DataFrame:
        """Generate patient data with potential outbreak patterns."""
        
        records = []
        
        for i in range(num_patients):
            record = self.generate_patient_record()
            
            # Simulate outbreak clustering
            if random.random() < outbreak_probability:
                # Add outbreak-like symptoms
                record["symptoms"].extend(["fever", "cough"])
                record["severity_score"] += random.uniform(2, 4)
                
                # Cluster in time (last 7 days)
                recent_date = datetime.now() - timedelta(days=random.randint(0, 7))
                record["visit_date"] = recent_date.isoformat()
                
                # Cluster in location
                record["location"] = "Rural_Hospital_A"  # Outbreak location
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    def save_sample_data(self, filename: str = "sample_patient_data.csv"):
        """Generate and save sample data."""
        df = self.generate_outbreak_scenario(num_patients=500)
        filepath = f"./data/raw/{filename}"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        df.to_csv(filepath, index=False)
        print(f"Sample data saved to {filepath}")
        return df

# Usage example
if __name__ == "__main__":
    generator = PatientDataGenerator()
    sample_data = generator.save_sample_data()
    print(f"Generated {len(sample_data)} patient records")
