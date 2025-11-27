"""
Async database connection management for EpiSPY.

This module provides async SQLAlchemy setup with PostgreSQL using asyncpg driver.
Includes connection pooling, session management, and health check functions.

Example usage:
    from src.database.connection import get_async_session, get_db
    from src.database.models import Location
    
    # Using dependency injection in FastAPI
    @router.get("/locations")
    async def get_locations(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Location))
        return result.scalars().all()
    
    # Using context manager
    async with get_async_session() as session:
        location = Location(name="Mumbai", ...)
        session.add(location)
        await session.commit()
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text, inspect
from typing import AsyncGenerator, Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager

from ..utils.config import settings
from ..utils.logger import api_logger
from .models import Base


# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


def get_database_url() -> str:
    """
    Get database URL, converting to async format if needed.
    
    Converts postgresql:// to postgresql+asyncpg:// for async operations.
    
    Returns:
        Database URL string for async SQLAlchemy
        
    Example:
        url = get_database_url()
        # Returns: "postgresql+asyncpg://user:pass@localhost/db"
    """
    db_url = settings.database_url
    
    # Convert postgresql:// to postgresql+asyncpg:// for async
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    return db_url


def create_engine() -> AsyncEngine:
    """
    Create and configure async SQLAlchemy engine.
    
    Configures connection pooling, echo mode, and pool settings
    based on environment configuration.
    
    Returns:
        Configured AsyncEngine instance
        
    Raises:
        ValueError: If database URL is invalid
        
    Example:
        engine = create_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    db_url = get_database_url()
    
    if not db_url:
        raise ValueError("DATABASE_URL not configured in environment")
    
    # Determine pool class based on database type
    pool_class = QueuePool if "postgresql" in db_url else NullPool
    
    # Engine configuration
    engine_kwargs = {
        "url": db_url,
        "echo": settings.debug,  # Log SQL queries in debug mode
        "future": True,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    }
    
    # Add pool settings for PostgreSQL
    if "postgresql" in db_url:
        engine_kwargs.update({
            "poolclass": pool_class,
            "pool_size": 10,  # Number of connections to maintain
            "max_overflow": 20,  # Maximum overflow connections
            "pool_timeout": 30,  # Timeout for getting connection from pool
        })
    
    _engine = create_async_engine(**engine_kwargs)
    
    api_logger.info(
        f"Async database engine created: "
        f"{db_url.split('@')[-1] if '@' in db_url else 'local'}"
    )
    
    return _engine


def get_async_session_factory() -> async_sessionmaker:
    """
    Get or create async session factory.
    
    Returns:
        Configured async_sessionmaker instance
        
    Example:
        session_factory = get_async_session_factory()
        async with session_factory() as session:
            # Use session
            pass
    """
    global _async_session_factory
    
    if _async_session_factory is not None:
        return _async_session_factory
    
    engine = create_engine()
    
    _async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    api_logger.info("Async session factory created")
    
    return _async_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session as context manager.
    
    Yields an async session and ensures proper cleanup.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        async with get_async_session() as session:
            result = await session.execute(select(Location))
            locations = result.scalars().all()
            # Session automatically committed/rolled back on exit
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database session.
    
    Use this as a dependency in FastAPI route handlers.
    Automatically handles session lifecycle and cleanup.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @router.get("/locations")
        async def get_locations(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Location))
            return result.scalars().all()
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    Creates all tables defined in models.py if they don't exist.
    Should be called once during application startup.
    
    Raises:
        Exception: If table creation fails
        
    Example:
        await init_db()
        # All tables from models.py are now created
    """
    try:
        engine = create_engine()
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        api_logger.info("Database tables initialized successfully")
        
    except Exception as e:
        api_logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Use with caution.
    Primarily for testing and development.
    
    Example:
        await drop_db()
        # All tables are now dropped
    """
    try:
        engine = create_engine()
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        api_logger.warning("All database tables dropped")
        
    except Exception as e:
        api_logger.error(f"Failed to drop database: {str(e)}")
        raise


async def check_db_health() -> Dict[str, Any]:
    """
    Check database connection health.
    
    Performs a simple query to verify database connectivity
    and returns health status information.
    
    Returns:
        Dictionary with health status information:
        - status: "healthy" or "unhealthy"
        - response_time_ms: Response time in milliseconds
        - error: Error message if unhealthy
        
    Example:
        health = await check_db_health()
        if health["status"] == "healthy":
            print(f"DB is healthy, response time: {health['response_time_ms']}ms")
    """
    import time
    
    start_time = time.time()
    
    try:
        engine = create_engine()
        
        async with engine.begin() as conn:
            # Simple query to check connectivity
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time_ms, 2),
            "database_url": get_database_url().split("@")[-1] if "@" in get_database_url() else "local",
        }
        
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "unhealthy",
            "response_time_ms": round(response_time_ms, 2),
            "error": str(e),
            "database_url": get_database_url().split("@")[-1] if "@" in get_database_url() else "local",
        }


async def get_table_info() -> Dict[str, Any]:
    """
    Get information about database tables.
    
    Returns metadata about all tables in the database including
    table names, column counts, and row counts.
    
    Returns:
        Dictionary with table information
        
    Example:
        info = await get_table_info()
        print(f"Tables: {info['tables']}")
        print(f"Total rows: {info['total_rows']}")
    """
    try:
        engine = create_engine()
        table_info = {
            "tables": [],
            "total_rows": 0,
        }
        
        async with engine.begin() as conn:
            # Get all table names
            inspector = inspect(engine.sync_engine)
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                # Get row count
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                row_count = result.scalar()
                
                table_info["tables"].append({
                    "name": table_name,
                    "row_count": row_count,
                })
                table_info["total_rows"] += row_count
        
        return table_info
        
    except Exception as e:
        api_logger.error(f"Failed to get table info: {str(e)}")
        return {
            "tables": [],
            "total_rows": 0,
            "error": str(e),
        }


async def close_db() -> None:
    """
    Close database connections and cleanup.
    
    Should be called during application shutdown to properly
    close all database connections.
    
    Example:
        await close_db()
        # All database connections are now closed
    """
    global _engine, _async_session_factory
    
    if _engine:
        await _engine.dispose()
        _engine = None
        api_logger.info("Database engine closed")
    
    _async_session_factory = None

