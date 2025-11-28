-- =============================================
-- EPISPY V2.0 - PATIENT HEALTH SYSTEM SCHEMA
-- =============================================

-- 1. PATIENTS TABLE (Core user information)
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    
    -- Emergency contact
    emergency_contact JSONB, -- {"name": "...", "phone": "..."}
    
    -- Account status
    email_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, deleted
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    -- Health profile (extended data)
    health_profile JSONB DEFAULT '{}'::jsonb,
    
    -- Location for weather correlation
    location GEOGRAPHY(POINT),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    
    -- Preferences
    notification_preferences JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patients_phone ON patients(phone);
CREATE INDEX idx_patients_location ON patients USING GIST(location);
CREATE INDEX idx_patients_city ON patients(city);

-- 2. HEALTH_REPORTS TABLE (Uploaded lab reports)
CREATE TABLE IF NOT EXISTS health_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Report metadata
    report_type VARCHAR(50) NOT NULL, -- blood_test, urine, xray, ecg, mri, etc
    test_date DATE NOT NULL,
    lab_name VARCHAR(255),
    doctor_name VARCHAR(255),
    
    -- File storage
    file_url VARCHAR(500), -- S3/cloud storage URL
    file_type VARCHAR(20), -- pdf, jpg, png
    file_size_bytes INTEGER,
    
    -- Extracted data (OCR + AI parsing)
    extracted_data JSONB DEFAULT '{}'::jsonb,
    
    -- AI analysis
    ai_analysis JSONB DEFAULT '{}'::jsonb,
    
    -- Processing status
    ocr_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    analysis_status VARCHAR(20) DEFAULT 'pending',
    
    -- Timestamps
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    
    -- Verification
    doctor_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(255),
    verified_at TIMESTAMP
);

CREATE INDEX idx_health_reports_patient ON health_reports(patient_id);
CREATE INDEX idx_health_reports_type ON health_reports(report_type);
CREATE INDEX idx_health_reports_date ON health_reports(test_date DESC);
CREATE INDEX idx_health_reports_extracted_data ON health_reports USING GIN(extracted_data);

-- 3. SYMPTOM_LOGS TABLE (Daily symptom tracking)
CREATE TABLE IF NOT EXISTS symptom_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Symptoms (JSONB array of symptoms with severity)
    symptoms JSONB NOT NULL,
    
    -- Overall severity (1-10)
    overall_severity INTEGER CHECK (overall_severity BETWEEN 1 AND 10),
    
    -- Additional notes
    notes TEXT,
    
    -- Photos (rashes, wounds, etc)
    photo_urls TEXT[], -- Array of image URLs
    
    -- Voice recording URL (patient describing symptoms)
    voice_recording_url VARCHAR(500),
    voice_transcript TEXT,
    
    -- AI prediction from symptoms
    predicted_conditions JSONB,
    
    -- Timestamps
    logged_at TIMESTAMP DEFAULT NOW(),
    symptom_start_date DATE
);

CREATE INDEX idx_symptom_logs_patient ON symptom_logs(patient_id);
CREATE INDEX idx_symptom_logs_date ON symptom_logs(logged_at DESC);
CREATE INDEX idx_symptom_logs_symptoms ON symptom_logs USING GIN(symptoms);

-- 4. PREDICTIONS TABLE (Health predictions/forecasts)
CREATE TABLE IF NOT EXISTS patient_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Prediction type
    prediction_type VARCHAR(50) NOT NULL,
    
    -- Predicted condition/event
    predicted_condition VARCHAR(255),
    
    -- Probability (0.0 to 1.0)
    probability DECIMAL(5, 4) CHECK (probability BETWEEN 0 AND 1),
    
    -- Confidence interval
    confidence_lower DECIMAL(5, 4),
    confidence_upper DECIMAL(5, 4),
    
    -- Risk level (for UI display)
    risk_level VARCHAR(20), -- LOW, MODERATE, HIGH, CRITICAL
    
    -- Timeframe
    prediction_timeframe VARCHAR(50), -- 24_hours, 7_days, 14_days, 30_days
    expected_onset_date DATE,
    
    -- Contributing factors
    factors JSONB,
    
    -- Recommendations
    recommendations TEXT[],
    
    -- Model metadata
    model_name VARCHAR(100),
    model_version VARCHAR(20),
    
    -- Timestamps
    generated_at TIMESTAMP DEFAULT NOW(),
    
    -- Outcome tracking (for model improvement)
    actual_outcome VARCHAR(50), -- confirmed, not_occurred, too_early
    outcome_recorded_at TIMESTAMP,
    prediction_accuracy DECIMAL(5, 4) -- Calculated after outcome known
);

CREATE INDEX idx_patient_predictions_patient ON patient_predictions(patient_id);
CREATE INDEX idx_patient_predictions_type ON patient_predictions(prediction_type);
CREATE INDEX idx_patient_predictions_date ON patient_predictions(generated_at DESC);
CREATE INDEX idx_patient_predictions_risk ON patient_predictions(risk_level);

-- 5. WEATHER_DATA_CACHE TABLE (Store weather for correlation)
CREATE TABLE IF NOT EXISTS weather_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city VARCHAR(100) NOT NULL,
    
    -- Weather parameters
    temperature_celsius DECIMAL(5, 2),
    humidity_percent INTEGER,
    wind_speed_kmh DECIMAL(5, 2),
    rainfall_mm DECIMAL(5, 2),
    pm25_aqi INTEGER, -- Air quality
    uv_index INTEGER,
    
    -- Weather condition
    condition VARCHAR(50), -- sunny, rainy, cloudy, stormy
    
    -- Disease risk multipliers (calculated)
    disease_multipliers JSONB,
    
    -- Timestamps
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    -- Cache management
    cached_until TIMESTAMP, -- Refresh after this time
    
    UNIQUE(city, recorded_at)
);

CREATE INDEX idx_weather_data_city ON weather_data_cache(city);
CREATE INDEX idx_weather_data_time ON weather_data_cache(recorded_at DESC);

-- 6. HOSPITAL_TRENDS_CACHE TABLE (Aggregate hospital data)
CREATE TABLE IF NOT EXISTS hospital_trends_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city VARCHAR(100) NOT NULL,
    
    -- Disease-specific trends
    disease_name VARCHAR(100) NOT NULL,
    case_count INTEGER,
    trend_direction VARCHAR(10), -- increasing, decreasing, stable
    trend_percentage DECIMAL(5, 2), -- +23%, -10%, etc
    
    -- Hospital capacity
    icu_occupancy_percent INTEGER,
    general_bed_occupancy_percent INTEGER,
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metadata
    data_source VARCHAR(255), -- Which hospitals/APIs
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(city, disease_name, period_start, period_end)
);

CREATE INDEX idx_hospital_trends_city ON hospital_trends_cache(city);
CREATE INDEX idx_hospital_trends_disease ON hospital_trends_cache(disease_name);
CREATE INDEX idx_hospital_trends_date ON hospital_trends_cache(period_end DESC);

-- 7. NOTIFICATIONS TABLE (Patient alerts)
CREATE TABLE IF NOT EXISTS patient_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Notification content
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50), -- prediction_alert, test_reminder, report_ready, emergency
    
    -- Priority
    priority VARCHAR(20), -- low, medium, high, critical
    
    -- Associated data
    related_prediction_id UUID REFERENCES patient_predictions(id),
    related_report_id UUID REFERENCES health_reports(id),
    
    -- Delivery channels
    channels TEXT[], -- ["email", "sms", "push", "voice"]
    
    -- Status
    sent_via_email BOOLEAN DEFAULT FALSE,
    sent_via_sms BOOLEAN DEFAULT FALSE,
    sent_via_push BOOLEAN DEFAULT FALSE,
    sent_via_voice BOOLEAN DEFAULT FALSE,
    
    -- User interaction
    read_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    action_taken VARCHAR(50), -- scheduled_test, called_doctor, etc
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    scheduled_for TIMESTAMP, -- Send at specific time
    sent_at TIMESTAMP
);

CREATE INDEX idx_patient_notifications_patient ON patient_notifications(patient_id);
CREATE INDEX idx_patient_notifications_created ON patient_notifications(created_at DESC);
CREATE INDEX idx_patient_notifications_priority ON patient_notifications(priority);
CREATE INDEX idx_patient_notifications_read ON patient_notifications(read_at) WHERE read_at IS NULL;

-- 8. TOKEN_BLACKLIST TABLE (Revoked JWT tokens)
CREATE TABLE IF NOT EXISTS token_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token TEXT NOT NULL UNIQUE,
    blacklisted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_token_blacklist_token ON token_blacklist(token);
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);

-- 9. AUDIT_LOG TABLE (Track all patient actions)
CREATE TABLE IF NOT EXISTS patient_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    
    -- Action details
    action VARCHAR(100) NOT NULL, -- login, report_upload, view_prediction, etc
    resource_type VARCHAR(50), -- report, prediction, profile
    resource_id UUID,
    
    -- Request metadata
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50), -- mobile, desktop, tablet
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_patient ON patient_audit_log(patient_id);
CREATE INDEX idx_audit_log_action ON patient_audit_log(action);
CREATE INDEX idx_audit_log_created ON patient_audit_log(created_at DESC);

-- =============================================
-- TRIGGERS FOR AUTO-UPDATED TIMESTAMPS
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- SAMPLE DATA (For testing)
-- =============================================

-- Insert sample patient
INSERT INTO patients (email, password_hash, phone, full_name, date_of_birth, gender, city, country)
VALUES (
    'test@epispy.ai',
    '$2b$12$KIXfP8lqOuO6mPRz7QfqPe8pHZHKV.qEh7Nk7xZJqFkPQf6qkqNMy', -- password: Test@1234
    '+919876543210',
    'Test Patient',
    '1985-06-15',
    'male',
    'Mumbai',
    'India'
);
