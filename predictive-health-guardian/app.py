import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# Page Config
st.set_page_config(
    page_title="Predictive Health Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background: linear-gradient(45deg, #FF4B4B, #FF914D);
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ Predictive Health Guardian")
    st.markdown("### AI Agents predict your 10yr disease risk in seconds")
with col2:
    st.image("https://img.icons8.com/fluency/96/heart-health.png", width=80)

st.divider()

# Sidebar - Controls & Presets
with st.sidebar:
    st.header("Patient Profile")
    
    # Presets
    st.subheader("Demo Presets")
    preset = st.selectbox(
        "Choose a Profile",
        ["Custom", "Healthy 30yo", "High-risk 45yo", "Diabetic 55yo"]
    )
    
    if preset == "Healthy 30yo":
        def_age, def_bmi, def_bp, def_sym = 30, 22.0, 115, "None"
    elif preset == "High-risk 45yo":
        def_age, def_bmi, def_bp, def_sym = 45, 29.0, 135, "Mild chest pain, fatigue"
    elif preset == "Diabetic 55yo":
        def_age, def_bmi, def_bp, def_sym = 55, 32.0, 145, "Frequent urination, excessive thirst"
    else:
        def_age, def_bmi, def_bp, def_sym = 25, 24.0, 120, "None"

    with st.form("patient_form"):
        age = st.slider("Age", 18, 100, def_age)
        bmi = st.number_input("BMI", 15.0, 50.0, def_bmi)
        bp_systolic = st.slider("Systolic BP (mmHg)", 90, 200, def_bp)
        symptoms = st.text_area("Symptoms", def_sym)
        
        submitted = st.form_submit_button("Analyze Health Risks 🚀")

# Main Content
if submitted:
    with st.spinner("🤖 AI Agents analyzing vitals & symptoms..."):
        # Simulate processing time for effect
        time.sleep(1.5)
        
        try:
            # Call API
            api_url = "http://localhost:8000/predict"
            payload = {
                "age": age,
                "bmi": bmi,
                "bp_systolic": bp_systolic,
                "symptoms": symptoms
            }
            
            # Try to connect to API, if fails, show friendly error
            try:
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    risks = data["risks"]
                    recommendations = data["recommendations"]
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.stop()
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Backend API is not running. Please run './run.sh' or 'python api.py'")
                st.stop()

            # Display Results
            st.success("Analysis Complete!")
            
            # Layout: Heatmap | Action Plan
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.subheader("📊 Disease Risk Heatmap")
                
                # Prepare data for chart
                risk_df = pd.DataFrame(list(risks.items()), columns=['Disease', 'Risk %'])
                
                # Color scale: Green to Red
                fig = px.bar(
                    risk_df, 
                    x='Risk %', 
                    y='Disease', 
                    orientation='h',
                    color='Risk %',
                    color_continuous_scale='RdYlGn_r',
                    range_color=[0, 100],
                    text='Risk %'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col_right:
                st.subheader("📋 AI Action Plan")
                st.info(recommendations)
                
                st.markdown("### 🧠 Agent Logic")
                with st.expander("View Agent Logs"):
                    st.code(f"""
[SymptomParser] Extracted: {symptoms}
[RiskPredictor] Vitals: Age {age}, BMI {bmi}, BP {bp_systolic}
[RiskPredictor] ML Model Output: {risks}
[ActionPlanner] Generating prioritized interventions...
                    """)

        except Exception as e:
            st.error(f"An error occurred: {e}")

else:
    # Empty State / Hero
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h2>👋 Welcome to Predictive Health Guardian</h2>
        <p>Enter patient vitals in the sidebar to generate a real-time health risk assessment.</p>
        <p style='color: #666;'>Powered by Multi-Agent AI & Synthetic Data</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "Built in 12hrs | HealthTech Hackathon 2025 | "
    "Predictive Health Guardian MVP"
    "</div>", 
    unsafe_allow_html=True
)
