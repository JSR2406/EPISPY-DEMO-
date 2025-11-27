# EpiSPY - Epidemic Prediction AI System

EpiSPY is an agentic AI system for epidemic prediction and risk assessment using anonymous patient data and LLM reasoning. It combines epidemiological modeling (SEIR), machine learning, and large language models to provide real-time epidemic monitoring and outbreak predictions.

## Features

- 🧠 **Agentic AI Reasoning**: Uses Ollama/LLM for intelligent analysis of epidemic patterns
- 📊 **SEIR Modeling**: Susceptible-Exposed-Infected-Recovered epidemic modeling
- 🔍 **Real-time Monitoring**: Continuous monitoring of patient data and outbreak risks
- 📈 **Risk Assessment**: Automated risk scoring and alert generation
- 🗺️ **Geographic Analysis**: Location-based outbreak prediction
- 🔒 **Privacy-First**: Patient data anonymization and secure processing
- 📱 **Dashboard**: Interactive Streamlit dashboard for visualization
- 🚀 **Production-Ready**: Docker support, authentication, rate limiting

## Architecture

```
EpiSPY/
├── src/
│   ├── api/              # FastAPI backend
│   ├── dashboard/        # Streamlit dashboard
│   ├── agents/           # Agentic AI components
│   ├── models/           # ML and SEIR models
│   ├── data/             # Data processing and storage
│   ├── integrations/     # External service clients
│   └── utils/            # Utilities and configuration
├── docker/               # Docker configurations
├── docs/                 # Documentation
└── scripts/              # Deployment and utility scripts
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- Ollama server (for LLM features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EpiSPY
   ```

2. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python -c "from src.data.storage.database import init_database; init_database()"
   ```

5. **Start the API**
   ```bash
   # Development mode
   python run_api.py --reload
   
   # Production mode
   python run_api.py --production --workers 4
   ```

6. **Start the dashboard** (in another terminal)
   ```bash
   streamlit run src/dashboard/Home.py
   ```

### Docker Deployment

```bash
# Using deployment script
python scripts/deploy.py --mode docker

# Or manually
cd docker
docker-compose up -d
```

## Configuration

### Environment Variables

Key configuration variables (see `env.example` for full list):

- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `OLLAMA_HOST`: Ollama server URL
- `SECRET_KEY`: Secret key for encryption
- `JWT_SECRET`: JWT token secret
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

### Generate Security Keys

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## API Documentation

Once the API is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### Example API Calls

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Submit patient data
curl -X POST http://localhost:8000/api/v1/data/patients \
  -H "Content-Type: application/json" \
  -d '{
    "patient_data": [{
      "patient_id": "P001",
      "visit_date": "2024-01-15T10:00:00",
      "location": "Hospital A",
      "age_group": "30-44",
      "symptoms": ["fever", "cough"],
      "severity_score": 7.5
    }],
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59"
  }'

# Get risk assessment
curl http://localhost:8000/api/v1/prediction/risk-assessment?location=Hospital%20A
```

## Development

### Project Structure

- `src/api/`: FastAPI application and routes
- `src/dashboard/`: Streamlit dashboard components
- `src/agents/`: Agentic AI reasoning components
- `src/models/`: ML models and SEIR epidemic model
- `src/data/`: Data processing, validation, and storage
- `src/integrations/`: External service integrations (Ollama, ChromaDB)
- `src/tests/`: Test suite

### Running Tests

```bash
pytest src/tests/ -v
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deployment

```bash
# Run deployment script
python scripts/deploy.py --mode full

# Or use Docker
cd docker
docker-compose up -d
```

## Features in Detail

### 1. Agentic AI Analysis

The system uses LLM (via Ollama) to analyze patient data and generate:
- Risk assessments
- Symptom pattern identification
- Geographic clustering
- Recommended actions

### 2. SEIR Epidemic Model

Implements the Susceptible-Exposed-Infected-Recovered model for:
- Outbreak probability prediction
- Peak date estimation
- Infection spread simulation

### 3. Data Processing Pipeline

- **Validation**: Ensures data quality and completeness
- **Normalization**: Standardizes data formats
- **Anonymization**: Protects patient privacy

### 4. Real-time Monitoring

- Continuous data ingestion
- Automated alert generation
- Risk score updates
- Trend analysis

## Security

- JWT-based authentication
- API key support
- Rate limiting
- Data anonymization
- Encrypted storage
- CORS configuration

## Monitoring

- Health check endpoints
- System metrics
- Component status monitoring
- Logging (file and console)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Check the [documentation](docs/)
- Review [API documentation](http://localhost:8000/docs)
- Open an issue on GitHub

## Acknowledgments

- Built with FastAPI, Streamlit, and Ollama
- Uses SEIR epidemic modeling
- Vector database powered by ChromaDB

---

**Note**: This is a production-ready system. Ensure you configure all security settings before deploying to production.
