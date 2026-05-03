"""Flask configuration for the Ticketing API.

This module provides configuration classes for different environments:
- Config: Base configuration
- DevelopmentConfig: For local development
- ProductionConfig: For production deployment
- TestingConfig: For running tests

Configuration is loaded from environment variables with fallback defaults.
"""
import os


def get_db_uri():
    """Get database URI from environment variables.

    Constructs the PostgreSQL connection string from environment
    variables or uses defaults (localhost:5432/postgres/ticketing).

    Returns:
        str: PostgreSQL connection URI
    """
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    db = os.environ.get("POSTGRES_DB", "ticketing")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


class Config:
    """Base application configuration.

    Provides default settings for database, Redis, and security.
    All settings can be overridden via environment variables.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = get_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
    EMAIL_SERVICE_URL = os.environ.get("EMAIL_SERVICE_URL", "http://localhost:5001")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing environment configuration.

    Uses in-memory SQLite database and separate Redis DB
    to avoid interfering with development data.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    REDIS_DB = 1
    EMAIL_SERVICE_URL = ""


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
