#!/bin/bash

echo "🚀 Starting Predictive Health Guardian..."

# 1. Generate Data
if [ ! -f "synthetic_health_data.csv" ]; then
    echo "📊 Generating synthetic data..."
    python data.py
fi

# 2. Start Backend (Background)
echo "🔌 Starting FastAPI Backend..."
uvicorn api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start
sleep 5

# 3. Start Frontend
echo "🖥️ Starting Streamlit UI..."
streamlit run app.py

# Cleanup on exit
kill $API_PID
