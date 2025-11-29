from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env before defining settings
# load_dotenv() - Removed to avoid potential null character issues, pydantic handles .env 

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    debug: bool = Field(True, validation_alias="DEBUG")

    # Database Configuration
    database_url: str = Field("postgresql://user:pass@localhost:5432/db", validation_alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", validation_alias="REDIS_URL")

    # AI Model Configuration
    ollama_host: str = Field("http://localhost:11434", validation_alias="OLLAMA_HOST")
    openai_api_key: str = Field("", validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field("", validation_alias="ANTHROPIC_API_KEY")

    # Security
    secret_key: str = Field("dev_secret", validation_alias="SECRET_KEY")
    encryption_key: str = Field("dev_enc_key", validation_alias="ENCRYPTION_KEY")
    jwt_secret: str = Field("dev_jwt_secret", validation_alias="JWT_SECRET")
    
    # Logging
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL") 
    log_file: str = Field("app.log", validation_alias="LOG_FILE")
    
    # External APIs
    deepgram_api_key: str = Field("", validation_alias="DEEPGRAM_API_KEY")
    weather_api_key: str = Field("", validation_alias="WEATHER_API_KEY")
    
    # Dashboard Configuration
    dashboard_port: int = Field(8501, validation_alias="DASHBOARD_PORT")
    dashboard_host: str = Field("localhost", validation_alias="DASHBOARD_HOST")

    class Config:
        env_file = ".env"
        extra = "ignore"
        # The next setting is helpful for V2 to explicitly map field names
        # allow_population_by_field_name = True # Removed for simplicity, validation_alias handles it
        
settings = Settings()
