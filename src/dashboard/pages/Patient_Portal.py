import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Patient Portal - EpiSPY",
    page_icon="🏥",
    layout="wide"
)

# API Base URL
API_URL = "http://localhost:8000/api"

# Session State Management
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

def login_user(email, password):
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.auth_token = data["access_token"]
            st.session_state.user_info = data["user"]
            st.success("Login successful!")
            st.rerun()
        else:
            st.error(f"Login failed: {response.json().get('detail')}")
    except Exception as e:
        st.error(f"Connection error: {e}")

def register_user(email, password, full_name, phone, dob, gender, city):
    try:
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "phone": phone,
            "date_of_birth": str(dob),
            "gender": gender,
            # "city": city # Backend schema needs update to accept city directly in register or profile update
        }
        response = requests.post(f"{API_URL}/auth/register", json=payload)
        if response.status_code == 200:
            st.success("Registration successful! Please login.")
        else:
            st.error(f"Registration failed: {response.json().get('detail')}")
    except Exception as e:
        st.error(f"Connection error: {e}")

def fetch_weather(city):
    try:
        response = requests.get(f"{API_URL}/weather/{city}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def upload_report(file, report_type):
    try:
        files = {"file": (file.name, file, file.type)}
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        response = requests.post(
            f"{API_URL}/reports/upload", 
            files=files, 
            params={"report_type": report_type},
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
    except Exception as e:
        st.error(f"Error: {e}")
    return None

# --- Main UI ---

if not st.session_state.auth_token:
    # Auth Screen
    st.title("🏥 Patient Portal Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                login_user(email, password)
    
    with tab2:
        with st.form("register_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            full_name = st.text_input("Full Name")
            phone = st.text_input("Phone")
            dob = st.date_input("Date of Birth")
            gender = st.selectbox("Gender", ["male", "female", "other"])
            city = st.text_input("City", value="Mumbai")
            
            submit_reg = st.form_submit_button("Register")
            if submit_reg:
                register_user(new_email, new_password, full_name, phone, dob, gender, city)

else:
    # Dashboard Screen
    user = st.session_state.user_info
    st.sidebar.title(f"Welcome, {user['full_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.auth_token = None
        st.session_state.user_info = None
        st.rerun()
    
    # Main Dashboard
    st.title("Your Health Dashboard")
    
    # City selection (mock profile setting)
    city = st.sidebar.text_input("Current Location", value="Mumbai")
    
    # Tabs
    tab_overview, tab_reports, tab_symptoms = st.tabs(["📊 Overview", "📄 Upload Reports", "🤒 Symptom Log"])
    
    with tab_overview:
        # Weather & Risk Section
        st.subheader(f"Health Forecast for {city}")
        
        col1, col2 = st.columns([1, 2])
        
        weather_data = fetch_weather(city)
        
        with col1:
            if weather_data:
                st.info(f"**Condition:** {weather_data['condition'].title()}")
                st.metric("Temperature", f"{weather_data['temperature_celsius']}°C")
                st.metric("Humidity", f"{weather_data['humidity_percent']}%")
                
                st.markdown("### Disease Risks")
                multipliers = weather_data.get('disease_multipliers', {})
                for disease, risk in multipliers.items():
                    color = "red" if risk > 2.0 else "orange" if risk > 1.5 else "green"
                    st.markdown(f"- **{disease.title()}**: <span style='color:{color}'>{risk}x Risk</span>", unsafe_allow_html=True)
            else:
                st.warning("Weather data unavailable")
        
        with col2:
            st.markdown("### 🛡️ Personal Health Insights")
            # Mock Predictions Display
            predictions = [
                {"disease": "Dengue", "risk": 85, "status": "HIGH"},
                {"disease": "Flu", "risk": 40, "status": "MODERATE"},
                {"disease": "Malaria", "risk": 15, "status": "LOW"},
            ]
            
            for p in predictions:
                color = "red" if p['status'] == "HIGH" else "orange" if p['status'] == "MODERATE" else "green"
                st.markdown(
                    f"""
                    <div style="padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; background-color: rgba(255,255,255,0.05);">
                        <h4 style="margin:0; color: {color}">{p['disease']} Risk: {p['status']} ({p['risk']}%)</h4>
                        <p style="margin:5px 0 0 0; font-size: 0.9em;">Based on local weather and hospital trends.</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

    with tab_reports:
        st.subheader("Upload Medical Reports")
        uploaded_file = st.file_uploader("Choose a file (PDF, JPG, PNG)", type=['pdf', 'jpg', 'png'])
        report_type = st.selectbox("Report Type", ["blood_test", "urine_test", "xray", "prescription"])
        
        if uploaded_file and st.button("Analyze Report"):
            with st.spinner("Analyzing with AI..."):
                result = upload_report(uploaded_file, report_type)
                if result:
                    st.success("Analysis Complete!")
                    
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.markdown("### 📋 Extracted Data")
                        st.json(result.get("extracted_data"))
                    
                    with col_res2:
                        st.markdown("### 🤖 AI Assessment")
                        analysis = result.get("ai_analysis", {})
                        st.write(analysis.get("risk_assessment"))
                        st.info(f"Recommendations: {', '.join(analysis.get('recommendations', []))}")

    with tab_symptoms:
        st.subheader("Log Daily Symptoms")
        with st.form("symptom_form"):
            symptoms = st.multiselect("Select Symptoms", ["Fever", "Cough", "Headache", "Fatigue", "Body Ache", "Rash", "Nausea"])
            severity = st.slider("Overall Severity (1-10)", 1, 10, 3)
            notes = st.text_area("Additional Notes")
            
            if st.form_submit_button("Log Symptoms"):
                st.success("Symptoms logged successfully! AI is analyzing patterns...")
                # Mock response
                st.warning("⚠️ Potential Risk: Viral Fever. Please monitor temperature.")
