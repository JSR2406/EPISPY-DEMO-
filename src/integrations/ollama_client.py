import os
from dotenv import load_dotenv
import ollama
from ollama import Client, ResponseError, RequestError

# --- Configuration Loading ---
load_dotenv() 
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
DEFAULT_MODEL = "mistral"

# --- Agentic Reasoning Function ---
# This is the function that must be present for the import to succeed
def get_ollama_analysis(model_output: str, model_name: str = DEFAULT_MODEL) -> str:
    """
    Takes structured prediction data and sends it to Ollama for natural language
    analysis and report generation (the reasoning layer).
    """
    
    # Check 1: Host configuration
    if not OLLAMA_HOST:
        return "🚨 ERROR: OLLAMA_HOST is not set in the .env file. Cannot run LLM reasoning."

    # The System Prompt: Defines the Agent's Role
    system_prompt = (
        "You are a specialized Epidemiological Decision Support Agent for MumbaiHacks. "
        "Your sole function is to analyze the following structured case predictions "
        "for the next 7 days. Identify the **highest risk location** (predicted cases > 15) "
        "and generate a short, professional, 3-point alert summary report "
        "formatted for immediate public health official review. Be concise and authoritative."
    )

    try:
        # 1. Initialize the client (connecting to the host from .env)
        client = Client(host=OLLAMA_HOST.replace('localhost', '127.0.0.1'))

        # 2. Use the chat endpoint for best agent performance
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"PREDICTION DATA:\n{model_output}"}
            ],
            options={"temperature": 0.1, "num_ctx": 4096}
        )
        
        # 3. Extract the final response content
        return response['message']['content']
    
    except ResponseError as e:
        return f"🚨 OLLAMA SERVER ERROR (Status {e.status_code}): Model '{model_name}' not ready or server failed to process. Details: {e.error}"
    
    except RequestError as e:
        return f"🚨 CRITICAL CONNECTION ERROR: Could not connect to Ollama at {OLLAMA_HOST}. Is the Ollama application running? Details: {e}"
        
    except Exception as e:
        return f"🚨 UNEXPECTED ERROR: {e}"

# --- Test Execution Block ---

def test_ollama_connection():
    """Runs a test case to verify integration."""
    print("--- STARTING OLLAMA INTEGRATION TEST ---")
    
    # Sample data that the LLM is instructed to analyze
    test_data = """
    Location_Code 3: Predicted Total Cases: 2
    Location_Code 5: Predicted Total Cases: 18 (HIGH RISK)
    Location_Code 9: Predicted Total Cases: 10
    """
    
    analysis_report = get_ollama_analysis(test_data)
    
    print("\n==============================================")
    print("      ✅ OLLAMA TEST REPORT RECEIVED")
    print("==============================================")
    print(analysis_report)
    print("==============================================")


if __name__ == '__main__':
    # We remove the execution wrapper here to prevent recursion during Uvicorn's reload
    # This file should only be run directly for testing, or imported by the app.
    # The Uvicorn process will now import the function successfully.
    test_ollama_connection()
