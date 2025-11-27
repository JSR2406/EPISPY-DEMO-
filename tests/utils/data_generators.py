"""
Data generators for creating realistic test epidemic data.

This module provides generators for creating synthetic epidemic data
that follows realistic patterns and distributions for testing ML models
and data processing pipelines.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


def generate_location_data(
    num_locations: int = 10,
    countries: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate realistic location data for testing.
    
    Args:
        num_locations: Number of locations to generate
        countries: Optional list of countries to use
        
    Returns:
        List of location dictionaries
    """
    if countries is None:
        countries = ["India", "USA", "UK", "Brazil", "China", "Japan", "Germany", "France"]
    
    major_cities = {
        "India": [("Mumbai", 19.0760, 72.8777, 12442373),
                  ("Delhi", 28.6139, 77.2090, 11007835),
                  ("Bangalore", 12.9716, 77.5946, 8443675)],
        "USA": [("New York", 40.7128, -74.0060, 8175133),
                ("Los Angeles", 34.0522, -118.2437, 3971883),
                ("Chicago", 41.8781, -87.6298, 2693976)],
        "UK": [("London", 51.5074, -0.1278, 8982000),
               ("Manchester", 53.4808, -2.2426, 547627),
               ("Birmingham", 52.4862, -1.8904, 1141816)],
    }
    
    locations = []
    for i in range(num_locations):
        country = random.choice(countries)
        
        if country in major_cities and random.random() < 0.7:
            # Use real city data
            city_name, lat, lon, pop = random.choice(major_cities[country])
        else:
            # Generate random city
            city_name = f"City{i+1}"
            lat = random.uniform(-90, 90)
            lon = random.uniform(-180, 180)
            pop = random.randint(10000, 10000000)
        
        locations.append({
            "id": uuid.uuid4(),
            "name": city_name,
            "latitude": lat,
            "longitude": lon,
            "population": pop,
            "country": country,
            "region": f"Region{random.randint(1, 10)}",
            "created_at": datetime.now() - timedelta(days=random.randint(0, 365)),
            "updated_at": datetime.now()
        })
    
    return locations


def generate_outbreak_events(
    location_ids: List[uuid.UUID],
    num_events: int = 50,
    disease_types: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Generate realistic outbreak event data.
    
    Simulates outbreak events with realistic patterns:
    - Cases follow exponential growth in early stages
    - Death rates vary by disease type
    - Recovery times follow typical patterns
    
    Args:
        location_ids: List of location IDs to assign events to
        num_events: Number of events to generate
        disease_types: Optional list of disease types
        start_date: Start date for events (defaults to 30 days ago)
        end_date: End date for events (defaults to now)
        
    Returns:
        List of outbreak event dictionaries
    """
    if disease_types is None:
        disease_types = ["COVID-19", "Dengue", "Malaria", "Influenza", "Cholera", "Measles"]
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=30)
    if end_date is None:
        end_date = datetime.now()
    
    # Disease characteristics
    disease_profiles = {
        "COVID-19": {"case_fatality_rate": 0.02, "recovery_days": 14, "severity_base": 7.0},
        "Dengue": {"case_fatality_rate": 0.001, "recovery_days": 7, "severity_base": 6.0},
        "Malaria": {"case_fatality_rate": 0.005, "recovery_days": 10, "severity_base": 6.5},
        "Influenza": {"case_fatality_rate": 0.001, "recovery_days": 7, "severity_base": 5.0},
        "Cholera": {"case_fatality_rate": 0.01, "recovery_days": 5, "severity_base": 7.5},
        "Measles": {"case_fatality_rate": 0.001, "recovery_days": 10, "severity_base": 6.0},
    }
    
    events = []
    for i in range(num_events):
        disease_type = random.choice(disease_types)
        profile = disease_profiles.get(disease_type, {
            "case_fatality_rate": 0.005,
            "recovery_days": 7,
            "severity_base": 6.0
        })
        
        # Generate timestamp
        time_diff = (end_date - start_date).total_seconds()
        timestamp = start_date + timedelta(seconds=random.uniform(0, time_diff))
        
        # Generate cases (exponential growth pattern)
        base_cases = random.randint(10, 500)
        growth_factor = random.uniform(1.1, 2.0)
        days_since_start = (timestamp - start_date).days
        cases = int(base_cases * (growth_factor ** min(days_since_start, 10)))
        cases = min(cases, 50000)  # Cap at realistic maximum
        
        # Calculate deaths and recoveries
        deaths = int(cases * profile["case_fatality_rate"] * random.uniform(0.5, 1.5))
        deaths = min(deaths, cases)
        
        recovery_rate = random.uniform(0.6, 0.9)
        recovered = int((cases - deaths) * recovery_rate)
        active_cases = cases - deaths - recovered
        
        # Calculate severity
        severity = profile["severity_base"] + random.uniform(-1.0, 1.0)
        severity = max(1.0, min(10.0, severity))
        
        events.append({
            "id": uuid.uuid4(),
            "location_id": random.choice(location_ids),
            "disease_type": disease_type,
            "cases": cases,
            "deaths": deaths,
            "recovered": recovered,
            "active_cases": active_cases,
            "timestamp": timestamp,
            "severity": severity,
            "created_at": timestamp,
            "updated_at": timestamp
        })
    
    return events


def generate_time_series_data(
    location_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
    daily_interval: bool = True,
    disease_type: str = "COVID-19"
) -> pd.DataFrame:
    """
    Generate time series data for a location.
    
    Creates realistic time series with trends, seasonality, and noise.
    
    Args:
        location_id: Location ID
        start_date: Start date for time series
        end_date: End date for time series
        daily_interval: If True, daily data; if False, weekly
        disease_type: Disease type
        
    Returns:
        DataFrame with time series data
    """
    dates = pd.date_range(start_date, end_date, freq="D" if daily_interval else "W")
    n_days = len(dates)
    
    # Generate base trend (exponential growth with plateau)
    t = np.arange(n_days)
    growth_rate = random.uniform(0.05, 0.15)
    plateau_day = random.randint(int(n_days * 0.6), int(n_days * 0.8))
    
    base_trend = np.where(
        t < plateau_day,
        np.exp(growth_rate * t),
        np.exp(growth_rate * plateau_day)
    )
    
    # Add seasonality (weekly pattern)
    seasonality = 1 + 0.2 * np.sin(2 * np.pi * t / 7)
    
    # Add noise
    noise = np.random.normal(0, 0.1, n_days)
    
    # Combine components
    cases = (base_trend * seasonality * (1 + noise)).astype(int)
    cases = np.maximum(cases, 0)  # Ensure non-negative
    
    # Generate deaths and recoveries
    case_fatality_rate = random.uniform(0.01, 0.03)
    recovery_rate = random.uniform(0.7, 0.9)
    
    deaths = (cases * case_fatality_rate * np.random.uniform(0.8, 1.2, n_days)).astype(int)
    recovered = ((cases - deaths) * recovery_rate * np.random.uniform(0.8, 1.2, n_days)).astype(int)
    active_cases = cases - deaths - recovered
    
    # Create DataFrame
    df = pd.DataFrame({
        "date": dates,
        "location_id": location_id,
        "disease_type": disease_type,
        "cases": cases,
        "deaths": deaths,
        "recovered": recovered,
        "active_cases": active_cases,
        "severity": np.random.uniform(5.0, 9.0, n_days)
    })
    
    return df


def generate_predictions(
    location_ids: List[uuid.UUID],
    num_predictions: int = 20,
    prediction_horizon_days: int = 14,
    model_versions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate prediction data for testing ML models.
    
    Args:
        location_ids: List of location IDs
        num_predictions: Number of predictions to generate
        prediction_horizon_days: Days ahead to predict
        model_versions: Optional list of model versions
        
    Returns:
        List of prediction dictionaries
    """
    if model_versions is None:
        model_versions = ["seir-v1.0.0", "ml-v2.0.0", "hybrid-v1.5.0"]
    
    predictions = []
    for i in range(num_predictions):
        location_id = random.choice(location_ids)
        model_version = random.choice(model_versions)
        
        # Generate realistic predictions
        base_cases = random.randint(100, 10000)
        predicted_cases = base_cases * random.uniform(0.8, 2.0)
        
        # Confidence varies by model
        confidence_map = {
            "seir-v1.0.0": random.uniform(0.7, 0.9),
            "ml-v2.0.0": random.uniform(0.75, 0.95),
            "hybrid-v1.5.0": random.uniform(0.8, 0.95)
        }
        confidence = confidence_map.get(model_version, random.uniform(0.7, 0.9))
        
        prediction_date = datetime.now() + timedelta(days=random.randint(1, prediction_horizon_days))
        
        predictions.append({
            "id": uuid.uuid4(),
            "location_id": location_id,
            "predicted_cases": int(predicted_cases),
            "confidence": confidence,
            "prediction_date": prediction_date,
            "model_version": model_version,
            "metadata_json": {
                "r0": random.uniform(1.5, 3.5),
                "peak_day": random.randint(7, 21),
                "peak_cases": int(predicted_cases * random.uniform(1.2, 2.0)),
                "growth_rate": random.uniform(0.1, 0.3)
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
    
    return predictions


def generate_risk_assessments(
    location_ids: List[uuid.UUID],
    num_assessments: int = 15
) -> List[Dict[str, Any]]:
    """
    Generate risk assessment data.
    
    Args:
        location_ids: List of location IDs
        num_assessments: Number of assessments to generate
        
    Returns:
        List of risk assessment dictionaries
    """
    from src.database.models import RiskLevel
    
    assessments = []
    for i in range(num_assessments):
        location_id = random.choice(location_ids)
        
        # Generate risk score
        risk_score = random.uniform(0.0, 10.0)
        
        # Determine risk level
        if risk_score < 3:
            risk_level = RiskLevel.LOW
        elif risk_score < 6:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 8:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        assessments.append({
            "id": uuid.uuid4(),
            "location_id": location_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "factors_json": {
                "case_growth_rate": random.uniform(0.0, 1.0),
                "population_density": random.uniform(0.0, 1.0),
                "healthcare_capacity": random.uniform(0.0, 1.0),
                "travel_restrictions": random.choice([0, 1]),
                "vaccination_rate": random.uniform(0.0, 1.0),
                "testing_capacity": random.uniform(0.0, 1.0)
            },
            "timestamp": datetime.now() - timedelta(hours=random.randint(0, 24)),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
    
    return assessments


def generate_patient_records(
    num_records: int = 100,
    locations: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Generate synthetic patient record data.
    
    Creates realistic patient records with symptoms, severity scores, and demographics.
    
    Args:
        num_records: Number of records to generate
        locations: Optional list of location names
        start_date: Start date for records
        end_date: End date for records
        
    Returns:
        DataFrame with patient records
    """
    if locations is None:
        locations = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=30)
    if end_date is None:
        end_date = datetime.now()
    
    symptoms_list = [
        ["fever", "cough"],
        ["fever", "headache"],
        ["cough", "sore throat"],
        ["fever", "cough", "difficulty breathing"],
        ["fever", "body aches"],
        ["headache", "nausea"],
        ["fever", "chills"],
        ["cough", "chest pain"]
    ]
    
    age_groups = ["0-18", "19-35", "36-50", "51-65", "66+"]
    
    records = []
    for i in range(num_records):
        visit_date = start_date + timedelta(
            seconds=random.uniform(0, (end_date - start_date).total_seconds())
        )
        
        symptoms = random.choice(symptoms_list)
        age_group = random.choice(age_groups)
        location = random.choice(locations)
        
        # Calculate severity score based on symptoms and age
        base_severity = len(symptoms) * 1.5
        if "difficulty breathing" in symptoms:
            base_severity += 2.0
        if age_group in ["51-65", "66+"]:
            base_severity += 1.0
        
        severity_score = min(10.0, base_severity + random.uniform(-1.0, 1.0))
        
        records.append({
            "patient_id": f"PAT{random.randint(10000, 99999)}",
            "visit_date": visit_date,
            "location": location,
            "latitude": random.uniform(19.0, 19.2),
            "longitude": random.uniform(72.8, 73.0),
            "age_group": age_group,
            "symptoms": symptoms,
            "severity_score": severity_score,
            "created_at": visit_date,
            "updated_at": visit_date
        })
    
    return pd.DataFrame(records)


def generate_alert_data(
    location_ids: List[uuid.UUID],
    num_alerts: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate alert data for testing.
    
    Args:
        location_ids: List of location IDs
        num_alerts: Number of alerts to generate
        
    Returns:
        List of alert dictionaries
    """
    from src.database.models import AlertSeverity, AlertStatus
    
    alerts = []
    alert_templates = {
        AlertSeverity.INFO: "Routine monitoring update for {location}",
        AlertSeverity.WARNING: "Elevated case counts detected in {location}",
        AlertSeverity.SEVERE: "Significant outbreak reported in {location}",
        AlertSeverity.CRITICAL: "CRITICAL: Major epidemic outbreak in {location}"
    }
    
    for i in range(num_alerts):
        location_id = random.choice(location_ids)
        severity = random.choice(list(AlertSeverity))
        status = random.choice(list(AlertStatus))
        
        message = alert_templates.get(severity, f"Alert for location {location_id}")
        
        alerts.append({
            "id": uuid.uuid4(),
            "location_id": location_id,
            "severity": severity,
            "message": message,
            "status": status,
            "recipient_list": [
                f"user{j}@example.com" for j in range(random.randint(1, 5))
            ],
            "acknowledged_at": datetime.now() if status != AlertStatus.ACTIVE else None,
            "created_at": datetime.now() - timedelta(hours=random.randint(0, 48)),
            "updated_at": datetime.now()
        })
    
    return alerts

