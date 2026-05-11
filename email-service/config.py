"""Configuration for the Email Auxiliary Service.

This module provides configuration classes for different environments.
All settings can be overridden via environment variables.
"""
import os


class Config:
    """Base application configuration.

    Provides default settings for the email service.
    """

    SERVICE_NAME = "email-service"
    SERVICE_HOST = os.environ.get("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT = int(os.environ.get("SERVICE_PORT", "5001"))

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    SMTP_ENABLED = os.environ.get("SMTP_ENABLED", "false").lower() == "true"
    SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "false").lower() == "true"
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@ticketing.com")

    PRINT_TO_CONSOLE = os.environ.get("PRINT_TO_CONSOLE", "true").lower() == "true"


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    LOG_LEVEL = "WARNING"


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    LOG_LEVEL = "DEBUG"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
