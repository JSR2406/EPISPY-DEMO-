"""SEIR epidemic model implementation."""
import numpy as np
import pandas as pd
from scipy.integrate import odeint
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class SEIRModel:
    """Susceptible-Exposed-Infected-Recovered epidemic model."""
    
    def __init__(
        self, 
        population: int = 100000,
        initial_infected: int = 10,
        initial_exposed: int = 20
    ):
        self.population = population
        self.initial_infected = initial_infected
        self.initial_exposed = initial_exposed
        self.initial_susceptible = population - initial_infected - initial_exposed
        self.initial_recovered = 0
        
        # Default parameters (can be tuned)
        self.beta = 0.5      # Transmission rate
        self.sigma = 0.2     # Incubation rate (1/incubation_period)
        self.gamma = 0.1     # Recovery rate (1/infectious_period)
        
    def seir_equations(self, y: List[float], t: float) -> List[float]:
        """SEIR differential equations."""
        S, E, I, R = y
        N = S + E + I + R
        
        dSdt = -self.beta * S * I / N
        dEdt = self.beta * S * I / N - self.sigma * E
        dIdt = self.sigma * E - self.gamma * I
        dRdt = self.gamma * I
        
        return [dSdt, dEdt, dIdt, dRdt]
    
    def simulate(self, days: int = 365) -> pd.DataFrame:
        """Run SEIR simulation."""
        # Initial conditions
        y0 = [
            self.initial_susceptible,
            self.initial_exposed, 
            self.initial_infected,
            self.initial_recovered
        ]
        
        # Time points
        t = np.linspace(0, days, days)
        
        # Solve ODE
        solution = odeint(self.seir_equations, y0, t)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'day': range(days),
            'susceptible': solution[:, 0],
            'exposed': solution[:, 1],
            'infected': solution[:, 2],
            'recovered': solution[:, 3],
            'date': [datetime.now() + timedelta(days=i) for i in range(days)]
        })
        
        # Calculate derived metrics
        results['new_infections'] = results['infected'].diff().fillna(0)
        results['reproduction_number'] = self.calculate_r_effective(results)
        results['outbreak_probability'] = self.calculate_outbreak_probability(results)
        
        return results
    
    def calculate_r_effective(self, results: pd.DataFrame) -> pd.Series:
        """Calculate effective reproduction number."""
        # Simplified R_effective calculation
        S = results['susceptible']
        N = self.population
        R0 = self.beta / self.gamma  # Basic reproduction number
        
        return R0 * (S / N)
    
    def calculate_outbreak_probability(self, results: pd.DataFrame) -> pd.Series:
        """Calculate outbreak probability based on current state."""
        infected = results['infected']
        exposed = results['exposed']
        
        # Normalize to probability (0-1)
        risk_score = (infected + exposed) / self.population
        
        # Apply sigmoid transformation for probability
        outbreak_prob = 1 / (1 + np.exp(-10 * (risk_score - 0.01)))
        
        return outbreak_prob
    
    def update_parameters(
        self, 
        transmission_rate: Optional[float] = None,
        incubation_rate: Optional[float] = None,
        recovery_rate: Optional[float] = None
    ):
        """Update model parameters based on real data."""
        if transmission_rate is not None:
            self.beta = transmission_rate
        if incubation_rate is not None:
            self.sigma = incubation_rate
        if recovery_rate is not None:
            self.gamma = recovery_rate
    
    def predict_outbreak_risk(
        self, 
        current_infected: int,
        days_ahead: int = 14
    ) -> Dict[str, float]:
        """Predict outbreak risk for next N days."""
        
        # Update initial conditions with current data
        self.initial_infected = current_infected
        
        # Run short-term simulation
        results = self.simulate(days=days_ahead)
        
        # Calculate risk metrics
        max_infected = results['infected'].max()
        peak_day = results.loc[results['infected'].idxmax(), 'day']
        final_outbreak_prob = results['outbreak_probability'].iloc[-1]
        
        return {
            'max_predicted_infected': max_infected,
            'peak_day': peak_day,
            'outbreak_probability': final_outbreak_prob,
            'recommendation': self.get_recommendation(final_outbreak_prob)
        }
    
    def get_recommendation(self, outbreak_prob: float) -> str:
        """Get action recommendation based on outbreak probability."""
        if outbreak_prob > 0.8:
            return "IMMEDIATE_ACTION_REQUIRED"
        elif outbreak_prob > 0.6:
            return "HIGH_ALERT"
        elif outbreak_prob > 0.4:
            return "MODERATE_ALERT"
        elif outbreak_prob > 0.2:
            return "LOW_ALERT"
        else:
            return "NORMAL_MONITORING"

# Usage example
if __name__ == "__main__":
    # Create model instance
    model = SEIRModel(population=50000, initial_infected=5)
    
    # Run simulation
    results = model.simulate(days=180)
    
    # Predict outbreak risk
    risk_assessment = model.predict_outbreak_risk(current_infected=10)
    
    print("Outbreak Risk Assessment:")
    print(f"Max predicted infected: {risk_assessment['max_predicted_infected']:.0f}")
    print(f"Peak day: {risk_assessment['peak_day']}")
    print(f"Outbreak probability: {risk_assessment['outbreak_probability']:.2%}")
    print(f"Recommendation: {risk_assessment['recommendation']}")
