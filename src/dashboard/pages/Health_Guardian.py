import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import os

# Page Config
st.set_page_config(
    page_title="Predictive Health Guardian | EpiSPY",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
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
            # Assuming the API is running on localhost:8000
            api_host = os.getenv("API_HOST", "localhost")
            api_port = os.getenv("API_PORT", "8000")
            api_url = f"http://{api_host}:{api_port}/api/v1/health-guardian/predict"
            

            payload = {
                "age": age,
                "bmi": bmi,
                "bp_systolic": bp_systolic,
                "symptoms": symptoms,
                "location": "New York" # Default for now, can be added to UI

            
            # Try to connect to API, if fails, show friendly error
            try:
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    risks = data["risks"]
                    recommendations = data["recommendations"]
                    processed_symptoms = data.get("processed_symptoms", "Processed.")
                    analysis = data.get("analysis", "")
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
                    st.stop()
            except requests.exceptions.ConnectionError:
                st.error(f"⚠️ Backend API is not running at {api_url}. Please ensure the API server is started.")
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
                if analysis:
                    st.info(f"**AI Insight:** {analysis}")
                st.markdown(recommendations)
                
                st.markdown("### 🧠 Agent Logic")
                with st.expander("View Agent Logs"):
                    st.code(f"""
[SymptomParser] Extracted: {symptoms}
[RiskPredictor] Vitals: Age {age}, BMI {bmi}, BP {bp_systolic}
[RiskPredictor] ML Model Output: {risks}
[ActionPlanner] Generating prioritized interventions...
[System] {processed_symptoms}
                    """)

        except Exception as e:
            st.error(f"An error occurred: {e}")

# ... (Previous imports)
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io
from src.agents.chat_agent import MultilingualHealthChat

# Initialize Chat Agent
chat_agent = MultilingualHealthChat()

# ... (Previous Page Config and CSS)

# --- Main Content ---
if submitted:
    # ... (Existing prediction logic) ...
    
    # --- Chatbot Section (New) ---
    st.markdown("---")
    st.subheader("💬 Chat with Dr. Epi (AI Health Assistant)")
    
    col_chat, col_voice = st.columns([4, 1])
    
    with col_voice:
        st.markdown("**🎙️ Voice Input**")
        audio = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop Recording",
            key='recorder'
        )
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle Voice Input
    if audio:
        st.warning("Voice transcription requires OpenAI Whisper Key. Please type for now.")
    
    # Handle Text Input
    if prompt := st.chat_input("Ask a follow-up question (English or Hindi)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Dr. Epi is thinking..."):
                # Context from prediction
                context = {
                    "age": age,
                    "risks": risks if 'risks' in locals() else {},
                    "symptoms": symptoms
                }
                response = chat_agent.get_response(prompt, context)
                st.markdown(response)
                
                # TTS Output (Optional)
                try:
                    tts = gTTS(text=response, lang='en') 
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                except:
                    pass
                    
        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    # Empty State / Hero
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h2>👋 Welcome to Predictive Health Guardian</h2>
        <p>Enter patient vitals in the sidebar to generate a real-time health risk assessment.</p>
        <p style='color: #666;'>Powered by Multi-Agent AI & Synthetic Data</p>
    </div>
    """, unsafe_allow_html=True)
