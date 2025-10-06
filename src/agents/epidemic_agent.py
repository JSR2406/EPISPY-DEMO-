# src/agents/epidemic_agent.py

import pandas as pd
# Import the client function we just created
from src.integrations.ollama_client import get_ollama_analysis 
# You'll likely also need config/helpers later
from src.utils.config import get_config 

# Dummy function to simulate loading the processed data
def load_processed_data():
    # In a real scenario, this would load the processed CSV from the data/processed dir
    try:
        data_path = 'data/processed/time_series_data.csv' 
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        print("Using simulated data load...")
        # Placeholder data needed for the example to run
        return pd.DataFrame({'Location_Code': [1, 5, 8], 'Has_Diagnosis': [0, 1, 0]})

# The core execution logic of your agent
def run_epidemic_agent():
    # 1. Perception/Data Ingestion (Placeholder)
    data_df = load_processed_data()
    
    # 2. Prediction/Cognition (Simulated for now, replace with actual ML model output later)
    simulated_prediction_output = """
    Location_Code 1 (North): Predicted Total Cases: 4
    Location_Code 2 (South): Predicted Total Cases: 12
    Location_Code 5 (Central): Predicted Total Cases: 18 
    Location_Code 8 (West): Predicted Total Cases: 9
    """
    
    # 3. Reasoning (The Ollama Call)
    print("\n--- Running Agentic Reasoning via Ollama ---")
    analysis_report = get_ollama_analysis(simulated_prediction_output)
    
    # 4. Action/Reporting
    print("\n==============================================")
    print("      ✅ EPIDEMIC ALERT SYSTEM REPORT")
    print("==============================================")
    print(analysis_report)


if __name__ == '__main__':
    # Add dotenv loading here if you haven't put it in a central config.py utility
    run_epidemic_agent()