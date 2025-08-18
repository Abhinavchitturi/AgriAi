# AgriAI Assistant UI - Configuration Example
# Copy this file to local_config.py and modify as needed

"""
Example configuration file showing all available options.
Copy this to 'local_config.py' and modify values as needed.
The main config.py will import from local_config.py if it exists.
"""

# ============================================================================
# API Configuration
# ============================================================================

API_CONFIG = {
    "BASE_URL": "http://localhost:8000",  # Backend FastAPI URL
    "TIMEOUT": 30,                        # Request timeout in seconds
    "RETRY_ATTEMPTS": 3,                  # Number of retry attempts
    "RETRY_DELAY": 1.0                    # Delay between retries in seconds
}

# ============================================================================
# Development Configuration
# ============================================================================

DEV_CONFIG = {
    "debug_mode": False,           # Enable debug mode
    "log_level": "INFO",          # Log level (DEBUG, INFO, WARNING, ERROR)
    "enable_mock_api": False      # Use mock API for testing
}

# ============================================================================
# Voice Configuration
# ============================================================================

VOICE_CONFIG = {
    "continuous": False,          # Continuous listening
    "interim_results": False,     # Show interim results
    "max_alternatives": 1,        # Maximum alternatives
    "timeout": 10,               # Voice timeout in seconds
    "phrase_time_limit": 30      # Max phrase duration in seconds
}

# ============================================================================
# UI Theme Configuration
# ============================================================================

UI_THEME = {
    "primary_color": "#4CAF50",
    "secondary_color": "#2E7D32", 
    "accent_color": "#ff6b6b",
    "background_color": "#f8f9fa",
    "text_color": "#333333",
    "border_radius": "15px",
    "shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
}

# ============================================================================
# Response Configuration
# ============================================================================

RESPONSE_CONFIG = {
    "max_answer_length": 1000,    # Maximum answer length to display
    "show_confidence": True,      # Show confidence scores
    "show_source": True,         # Show source information
    "enable_followup": True      # Enable follow-up questions
}

# ============================================================================
# Chat History Configuration
# ============================================================================

HISTORY_CONFIG = {
    "max_items": 20,             # Maximum history items to store
    "display_items": 5,          # Number of items to display by default
    "enable_export": True,       # Enable history export feature
    "auto_save": True           # Automatically save conversations
}

# ============================================================================
# Additional Language Support
# ============================================================================

# Add more languages here if needed
CUSTOM_LANGUAGES = {
    "🇮🇳 ਪੰਜਾਬੀ (Punjabi)": {
        "code": "pa",
        "name": "ਪੰਜਾਬੀ",
        "voice_lang": "pa-IN",
        "rtl": False
    },
    "🇮🇳 ଓଡ଼ିଆ (Odia)": {
        "code": "or",
        "name": "ଓଡ଼ିଆ",
        "voice_lang": "or-IN",
        "rtl": False
    }
}

# ============================================================================
# Custom UI Text
# ============================================================================

CUSTOM_UI_TEXT = {
    "app_title": "🌾 AgriAI Assistant",
    "app_subtitle": "Your intelligent farming companion",
    "welcome_message": "Ask anything about agriculture",
    "footer_message": "Built with ❤️ for farmers worldwide"
}

# ============================================================================
# Feature Flags
# ============================================================================

FEATURE_FLAGS = {
    "enable_voice_input": True,       # Enable voice input feature
    "enable_history_export": True,    # Enable chat history export
    "enable_suggestions": True,       # Enable query suggestions
    "enable_offline_mode": False,     # Enable offline mode
    "enable_analytics": False,        # Enable usage analytics
    "mobile_optimized": True          # Enable mobile optimizations
}

# ============================================================================
# Performance Settings
# ============================================================================

PERFORMANCE_CONFIG = {
    "enable_caching": True,           # Enable response caching
    "cache_ttl": 300,                # Cache TTL in seconds
    "lazy_loading": True,            # Enable lazy loading of components
    "compress_responses": True        # Compress API responses
}

# ============================================================================
# Security Settings
# ============================================================================

SECURITY_CONFIG = {
    "enable_rate_limiting": True,     # Enable rate limiting
    "rate_limit_per_minute": 30,     # Max requests per minute
    "session_timeout": 30,           # Session timeout in minutes
    "sanitize_input": True,          # Sanitize user input
    "enable_csrf_protection": False  # CSRF protection (for future use)
}

# ============================================================================
# External Services (Optional)
# ============================================================================

EXTERNAL_SERVICES = {
    "weather_api_key": "",           # Weather service API key
    "maps_api_key": "",             # Maps service API key
    "translation_api_key": "",       # Translation service API key
    "analytics_api_key": ""          # Analytics service API key
}

# ============================================================================
# Error Handling
# ============================================================================

ERROR_CONFIG = {
    "show_detailed_errors": False,    # Show detailed error messages
    "auto_retry": True,              # Automatically retry failed requests
    "fallback_responses": True,       # Use fallback responses when API fails
    "error_logging": True            # Log errors to console
}

# ============================================================================
# Customization Options
# ============================================================================

CUSTOMIZATION = {
    "custom_css_file": "",           # Path to custom CSS file
    "custom_logo_path": "",          # Path to custom logo
    "favicon_path": "",              # Path to custom favicon
    "custom_fonts": []               # List of custom font URLs
}

# ============================================================================
# Database Configuration (for future use)
# ============================================================================

DATABASE_CONFIG = {
    "type": "sqlite",                # Database type
    "url": "sqlite:///agri_ai.db",  # Database URL
    "pool_size": 5,                 # Connection pool size
    "echo_queries": False           # Echo SQL queries (debug)
}

# ============================================================================
# Deployment Configuration
# ============================================================================

DEPLOYMENT_CONFIG = {
    "streamlit_port": 8501,          # Streamlit server port
    "streamlit_host": "localhost",   # Streamlit server host
    "enable_server_stats": False,    # Enable server statistics
    "max_upload_size": 50,          # Max file upload size in MB
    "enable_wide_mode": False        # Enable wide mode by default
}

# ============================================================================
# Content Moderation (for future use)
# ============================================================================

MODERATION_CONFIG = {
    "enable_content_filter": False,  # Enable content filtering
    "blocked_words": [],            # List of blocked words
    "max_query_length": 500,        # Maximum query length
    "min_query_length": 3           # Minimum query length
}

# ============================================================================
# Notifications (for future use)
# ============================================================================

NOTIFICATION_CONFIG = {
    "enable_notifications": False,   # Enable push notifications
    "notification_service_url": "", # Notification service URL
    "default_notification_sound": True  # Play sound for notifications
}

# ============================================================================
# Backup and Recovery
# ============================================================================

BACKUP_CONFIG = {
    "enable_auto_backup": False,     # Enable automatic backups
    "backup_interval": 24,          # Backup interval in hours
    "backup_location": "./backups", # Backup directory
    "max_backup_files": 7           # Maximum backup files to keep
}

# ============================================================================
# How to Use This Configuration
# ============================================================================

"""
1. Copy this file to 'local_config.py'
2. Modify the values you want to change
3. The main config.py will automatically import your local settings
4. Restart the application for changes to take effect

Example local_config.py:

# My custom configuration
API_CONFIG = {
    "BASE_URL": "https://my-api.com",
    "TIMEOUT": 60
}

UI_THEME = {
    "primary_color": "#FF5722"  # Orange theme
}

FEATURE_FLAGS = {
    "enable_voice_input": False  # Disable voice input
}
"""