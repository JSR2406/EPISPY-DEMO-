# EpiSPY V2.0 - Build & Integration Guide

This guide details the steps to build and integrate the EpiSPY V2.0 Personal Health Enhancement system, covering both the FastAPI Backend and the React Frontend.

## 🏗️ Backend Build (FastAPI)

The backend has been structured to support the new Patient Health System.

### 1. Environment Setup
Ensure your `.env` file contains the following keys:
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/epispy

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production

# External APIs
OPENWEATHER_API_KEY=your_openweather_key
OPENAI_API_KEY=your_openai_key
AWS_ACCESS_KEY=your_aws_key
AWS_SECRET_KEY=your_aws_secret
S3_BUCKET_NAME=epispy-reports
```

### 2. Database Migration
Run the SQL migration script to create the necessary tables:
```bash
# If using PostgreSQL directly
psql -U postgres -d epispy < database/migrations/add_patient_health_system.sql
```

### 3. Service Implementation Status
The following services have been implemented in `src/`:
- **Auth**: `src/auth/` (JWT, Password Hashing, Routes)
- **Weather**: `src/weather/` (OpenWeatherMap Integration)
- **Hospital**: `src/hospital/` (Disease Trend Aggregation)
- **Reports**: `src/reports/` (OCR & AI Analysis)
- **ML**: `src/ml/` (Personal Risk Calculator)
- **Notifications**: `src/notifications/` (Alert System)

### 4. Running the Backend
```bash
python run_api.py --reload
```
The API will be available at `http://localhost:8000`.

---

## 💻 Frontend Build (React)

We will build a modern React Patient Portal to replace/augment the Streamlit dashboard.

### 1. Initialization
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install axios react-router-dom @heroicons/react recharts framer-motion clsx tailwind-merge
```

### 2. Tailwind CSS Setup
Initialize Tailwind CSS for styling:
```bash
npx tailwindcss init -p
```
Configure `tailwind.config.js` and `index.css`.

### 3. Project Structure
```
frontend/src/
├── auth/           # Login, Register, ProtectedRoute
├── components/     # Reusable UI components (Cards, Charts)
├── pages/          # Dashboard, Reports, Symptoms
├── context/        # AuthContext, ThemeContext
└── api/            # Axios instance & API calls
```

### 4. Key Components to Build
1.  **Auth**: `Register.tsx`, `Login.tsx`
2.  **Dashboard**: `Dashboard.tsx` (Main view with widgets)
3.  **Widgets**:
    -   `RiskScoreGauge.tsx`: Visual risk indicator.
    -   `WeatherImpactCard.tsx`: Shows weather-health correlation.
    -   `SymptomLogger.tsx`: Form to log daily symptoms.

### 5. Integration Flow
1.  **Login**: Frontend sends credentials to `/api/auth/login` -> Stores JWT in localStorage.
2.  **Dashboard Load**:
    -   Fetch User Profile -> `/api/auth/me`
    -   Fetch Weather -> `/api/weather/{city}`
    -   Fetch Risks -> `/api/v1/health-guardian/predict` (or new ML endpoint)
3.  **Report Upload**:
    -   User selects file -> POST to `/api/reports/upload`
    -   Backend processes & returns JSON -> Frontend displays results.

---

## 🔄 Overall Integration Steps

1.  **Connect Frontend to Backend**:
    -   Configure CORS in `src/api/main.py` to allow requests from `http://localhost:5173` (Vite default).
    -   Set up Axios interceptors in React to attach the JWT token to every request.

2.  **End-to-End Testing**:
    -   **Scenario A**: New user registers -> Logs in -> Sees empty dashboard with Weather data.
    -   **Scenario B**: User uploads a blood test PDF -> Backend extracts "Low Platelets" -> Dashboard updates Dengue Risk to "HIGH".
    -   **Scenario C**: User logs "Fever" symptom -> System alerts "Possible Viral Infection".

3.  **Deployment**:
    -   **Backend**: Dockerize FastAPI app.
    -   **Frontend**: Build static assets (`npm run build`) and serve via Nginx or S3.
    -   **Database**: Managed PostgreSQL (RDS/Supabase).

---

**Next Action**: I will now proceed to scaffold the React Frontend application structure.
