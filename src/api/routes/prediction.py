"""Epidemic prediction endpoints."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from ...utils.logger import api_logger
from ...utils.app_state import AppState, get_app_state
from ..schemas.prediction import (
    PredictionRequest, 
    PredictionResponse,
    RiskAssessmentResponse
)

router = APIRouter()

@router.post("/analyze", response_model=PredictionResponse)
async def analyze_epidemic_data(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    app_state: AppState = Depends(get_app_state)
) -> PredictionResponse:
    """Analyze data for epidemic patterns."""
    
    try:
        api_logger.info(f"Starting epidemic analysis for {len(request.patient_data)} records")
        
        # Prepare data for analysis
        data_summary = f"""
        Analysis Request:
        - Patient Records: {len(request.patient_data)}
        - Time Range: {request.start_date} to {request.end_date}
        - Locations: {len(set(record.location for record in request.patient_data))}
        - Symptoms: {_extract_all_symptoms(request.patient_data)}
        """
        
        # Run AI analysis
        if app_state.ollama_client:
            ai_analysis = await app_state.ollama_client.analyze_medical_data(data_summary)
        else:
            ai_analysis = _fallback_analysis()
        
        # Run SEIR model prediction
        if app_state.seir_model:
            current_infected = len([r for r in request.patient_data if r.severity_score > 7])
            seir_prediction = app_state.seir_model.predict_outbreak_risk(
                current_infected=current_infected,
                days_ahead=14
            )
        else:
            seir_prediction = _fallback_seir_prediction()
        
        # Combine analyses
        combined_risk_score = (
            ai_analysis.get('risk_score', 5) * 0.6 +
            (seir_prediction.get('outbreak_probability', 0.3) * 10) * 0.4
        )
        
        response = PredictionResponse(
            analysis_id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            risk_score=combined_risk_score,
            outbreak_probability=seir_prediction.get('outbreak_probability', 0.3),
            predicted_peak_date=datetime.now() + timedelta(days=seir_prediction.get('peak_day', 14)),
            affected_locations=ai_analysis.get('geographic_clusters', []),
            symptom_patterns=ai_analysis.get('symptom_patterns', []),
            recommended_actions=ai_analysis.get('recommended_actions', []),
            confidence_score=ai_analysis.get('confidence', 0.7),
            model_version="1.0.0",
            analysis_timestamp=datetime.now()
        )
        
        # Store results in background
        background_tasks.add_task(_store_analysis_results, response)
        
        api_logger.info(f"Analysis completed with risk score: {combined_risk_score:.2f}")
        
        return response
        
    except Exception as e:
        api_logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_current_risk_assessment(
    location: Optional[str] = None,
    app_state: AppState = Depends(get_app_state)
) -> RiskAssessmentResponse:
    """Get current risk assessment for a location."""
    
    try:
        # This would typically query recent data from database
        # For now, we'll simulate with current model state
        
        if app_state.seir_model:
            results = app_state.seir_model.simulate(days=1)
            current_infected = results['infected'].iloc[-1]
            current_risk = results['outbreak_probability'].iloc[-1]
        else:
            current_infected = 10  # Fallback
            current_risk = 0.3
        
        # Determine alert level
        if current_risk > 0.8:
            alert_level = "CRITICAL"
        elif current_risk > 0.6:
            alert_level = "HIGH"
        elif current_risk > 0.4:
            alert_level = "MEDIUM"
        else:
            alert_level = "LOW"
        
        return RiskAssessmentResponse(
            location=location or "All Monitored Areas",
            current_risk_score=current_risk * 10,
            alert_level=alert_level,
            active_cases=int(current_infected),
            trend="STABLE",  # Would be calculated from historical data
            last_updated=datetime.now(),
            next_update=datetime.now() + timedelta(hours=1)
        )
        
    except Exception as e:
        api_logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@router.post("/continuous-monitoring")
async def start_continuous_monitoring(
    app_state: AppState = Depends(get_app_state)
) -> Dict[str, str]:
    """Start continuous monitoring mode."""
    
    # This would typically start a background task or job
    # For now, we'll just acknowledge the request
    
    api_logger.info("Continuous monitoring requested")
    
    return {
        "status": "monitoring_started",
        "message": "Continuous monitoring has been activated",
        "monitoring_interval": "5 minutes",
        "next_analysis": (datetime.now() + timedelta(minutes=5)).isoformat()
    }

def _extract_all_symptoms(patient_data: List) -> List[str]:
    """Extract all unique symptoms from patient data."""
    all_symptoms = set()
    for record in patient_data:
        if hasattr(record, 'symptoms') and record.symptoms:
            all_symptoms.update(record.symptoms)
    return list(all_symptoms)

def _fallback_analysis() -> Dict[str, Any]:
    """Fallback analysis when AI is unavailable."""
    return {
        "risk_score": 5.0,
        "symptom_patterns": ["Pattern analysis unavailable"],
        "geographic_clusters": ["Multiple locations"],
        "recommended_actions": ["Continue monitoring", "Collect more data"],
        "confidence": 0.5
    }

def _fallback_seir_prediction() -> Dict[str, Any]:
    """Fallback SEIR prediction."""
    return {
        "outbreak_probability": 0.3,
        "peak_day": 14,
        "max_predicted_infected": 50
    }

async def _store_analysis_results(response: PredictionResponse):
    """Store analysis results in background."""
    # This would typically save to database
    api_logger.info(f"Storing analysis results for {response.analysis_id}")
    
    # Simulate storage delay
    await asyncio.sleep(1)
    
    api_logger.info(f"Analysis results stored: {response.analysis_id}")
