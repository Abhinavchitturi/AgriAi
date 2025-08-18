"""
Centralized configuration management for Agriculture AI Assistant
Loads all environment variables and provides them to the application
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration class"""
    
    # ==================================================
    # ENVIRONMENT SETTINGS
    # ==================================================
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # ==================================================
    # APPLICATION SETTINGS
    # ==================================================
    APP_NAME = os.getenv("APP_NAME", "Agriculture AI Assistant")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # ==================================================
    # API SERVER SETTINGS
    # ==================================================
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # ==================================================
    # CORS SETTINGS
    # ==================================================
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
    CORS_METHODS = os.getenv("CORS_METHODS", "*").split(",")
    CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(",")
    
    # ==================================================
    # LOGGING SETTINGS
    # ==================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE = os.getenv("LOG_FILE", "logs/agriculture_ai.log")
    
    # ==================================================
    # OPENAI SETTINGS
    # ==================================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # ==================================================
    # EMBEDDING MODEL SETTINGS
    # ==================================================
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # ==================================================
    # LLM SETTINGS
    # ==================================================
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_TEMPERATURE_ZERO = float(os.getenv("LLM_TEMPERATURE_ZERO", "0.0"))
    
    # ==================================================
    # GOOGLE API SETTINGS
    # ==================================================
    GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # ==================================================
    # VISUAL CROSSING WEATHER API SETTINGS
    # ==================================================
    VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API_KEY")
    
    # ==================================================
    # OPENWEATHER API SETTINGS
    # ==================================================
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    # ==================================================
    # RAG SYSTEM SETTINGS
    # ==================================================
    MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "15000"))
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "150"))
    OVERLAP_SIZE = int(os.getenv("OVERLAP_SIZE", "30"))
    
    # ==================================================
    # CACHE SETTINGS
    # ==================================================
    WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "3600"))
    GEOCODE_CACHE_TTL = int(os.getenv("GEOCODE_CACHE_TTL", "86400"))
    SOIL_CACHE_TTL = int(os.getenv("SOIL_CACHE_TTL", "86400"))
    
    # ==================================================
    # UI SETTINGS
    # ==================================================
    UI_TIMEOUT = int(os.getenv("UI_TIMEOUT", "30"))
    UI_RETRY_ATTEMPTS = int(os.getenv("UI_RETRY_ATTEMPTS", "3"))
    UI_RETRY_DELAY = int(os.getenv("UI_RETRY_DELAY", "1"))
    ENABLE_MOCK_API = os.getenv("ENABLE_MOCK_API", "false").lower() == "true"
    
    # ==================================================
    # VOICE SETTINGS
    # ==================================================
    VOICE_CONTINUOUS = os.getenv("VOICE_CONTINUOUS", "false").lower() == "true"
    VOICE_INTERIM_RESULTS = os.getenv("VOICE_INTERIM_RESULTS", "false").lower() == "true"
    VOICE_MAX_ALTERNATIVES = int(os.getenv("VOICE_MAX_ALTERNATIVES", "1"))
    VOICE_TIMEOUT = int(os.getenv("VOICE_TIMEOUT", "10"))
    VOICE_PHRASE_TIME_LIMIT = int(os.getenv("VOICE_PHRASE_TIME_LIMIT", "30"))
    
    # ==================================================
    # ENVIRONMENT-SPECIFIC OVERRIDES
    # ==================================================
    @classmethod
    def get_debug(cls) -> bool:
        """Get debug setting based on environment"""
        if cls.ENVIRONMENT == "development":
            return os.getenv("DEV_DEBUG", "true").lower() == "true"
        elif cls.ENVIRONMENT == "production":
            return os.getenv("PROD_DEBUG", "false").lower() == "true"
        elif cls.ENVIRONMENT == "testing":
            return os.getenv("TEST_DEBUG", "true").lower() == "true"
        return cls.DEBUG
    
    @classmethod
    def get_log_level(cls) -> str:
        """Get log level based on environment"""
        if cls.ENVIRONMENT == "development":
            return os.getenv("DEV_LOG_LEVEL", "INFO")
        elif cls.ENVIRONMENT == "production":
            return os.getenv("PROD_LOG_LEVEL", "INFO")
        elif cls.ENVIRONMENT == "testing":
            return os.getenv("TEST_LOG_LEVEL", "INFO")
        return cls.LOG_LEVEL
    
    # ==================================================
    # VALIDATION METHODS
    # ==================================================
    @classmethod
    def validate_required_keys(cls) -> list:
        """Validate that all required API keys are present"""
        missing_keys = []
        
        if not cls.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        
        if not cls.GOOGLE_TRANSLATE_API_KEY:
            missing_keys.append("GOOGLE_TRANSLATE_API_KEY")
        
        if not cls.VISUAL_CROSSING_API_KEY:
            missing_keys.append("VISUAL_CROSSING_API_KEY")
        
        return missing_keys
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def is_testing(cls) -> bool:
        """Check if running in testing environment"""
        return cls.ENVIRONMENT.lower() == "testing"

# Create global config instance
config = Config()

# Export commonly used config values for backward compatibility
OPENAI_API_KEY = config.OPENAI_API_KEY
GOOGLE_TRANSLATE_API_KEY = config.GOOGLE_TRANSLATE_API_KEY
VISUAL_CROSSING_API_KEY = config.VISUAL_CROSSING_API_KEY
API_BASE_URL = config.API_BASE_URL
