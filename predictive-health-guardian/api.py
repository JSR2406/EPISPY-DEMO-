from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import HealthAgents
import uvicorn

app = FastAPI(
    title="Predictive Health Guardian API",
    description="AI-powered disease risk prediction API",
    version="1.0.0"
)

# Global instance
health_agents = HealthAgents()

class PatientData(BaseModel):
    age: int
    bmi: float
    bp_systolic: int
    symptoms: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "Predictive Health Guardian API is running"}

@app.post("/predict")
def predict_risk(data: PatientData):
    try:
        result = health_agents.get_analysis(
            data.age, 
            data.bmi, 
            data.bp_systolic, 
            data.symptoms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
