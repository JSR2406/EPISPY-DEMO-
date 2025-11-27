"""Database connection and utilities."""
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Optional
from datetime import datetime
import os

from ...utils.config import settings
from ...utils.logger import api_logger

Base = declarative_base()

# Database engine (lazy initialization)
_engine: Optional[any] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_engine():
    """Get or create database engine."""
    global _engine
    
    if _engine is None:
        database_url = settings.database_url
        
        # SQLite-specific configuration
        if database_url.startswith("sqlite"):
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.debug
            )
        else:
            # PostgreSQL or other databases
            _engine = create_engine(
                database_url,
                pool_pre_ping=True,
                echo=settings.debug
            )
        
        api_logger.info(f"Database engine created: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    return _engine


def get_session_local():
    """Get or create session factory."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_database_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


def init_database():
    """Initialize database tables."""
    try:
        engine = get_database_engine()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        api_logger.info("Database tables initialized")
        
    except Exception as e:
        api_logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db() -> Session:
    """
    Dependency for getting database session.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


# Database Models
class PatientRecordModel(Base):
    """Patient record database model."""
    __tablename__ = "patient_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    visit_date = Column(DateTime, nullable=False, index=True)
    location = Column(String, index=True, nullable=False)
    age_group = Column(String)
    symptoms = Column(Text)  # JSON string
    severity_score = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AnalysisResultModel(Base):
    """Analysis result database model."""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, unique=True, index=True, nullable=False)
    risk_score = Column(Float, nullable=False)
    outbreak_probability = Column(Float, nullable=False)
    predicted_peak_date = Column(DateTime)
    affected_locations = Column(Text)  # JSON string
    symptom_patterns = Column(Text)  # JSON string
    recommended_actions = Column(Text)  # JSON string
    confidence_score = Column(Float)
    model_version = Column(String)
    analysis_timestamp = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class AlertModel(Base):
    """Alert database model."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True, nullable=False)
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    location = Column(String, index=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

