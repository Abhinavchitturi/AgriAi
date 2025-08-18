# Environment Setup Guide

This guide will help you set up environment variables for the Agriculture AI Assistant project and remove all hardcoded values from your code.

## 🚀 Quick Setup

### 1. Run the Setup Script
```bash
python setup_env.py
```

This will automatically create a `.env` file from the template and remove the template file.

### 2. Manual Setup (Alternative)
If you prefer to do it manually:

1. Copy `env_template.txt` to `.env`
2. Update the API keys with your actual values
3. Delete `env_template.txt`

## 📋 Required API Keys

### OpenAI API Key
- **Required**: Yes
- **Purpose**: RAG system, language processing
- **Get it from**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Format**: `sk-proj-...`

### Google Translate API Key
- **Required**: Yes
- **Purpose**: Language translation services
- **Get it from**: [Google Cloud Console](https://console.cloud.google.com/)
- **Format**: `AIzaSy...`

### Google Maps API Key
- **Required**: Yes
- **Purpose**: Geocoding and location services
- **Get it from**: [Google Cloud Console](https://console.cloud.google.com/)
- **Format**: `AIzaSy...`

### Visual Crossing Weather API Key
- **Required**: Yes
- **Purpose**: Weather data and forecasts
- **Get it from**: [Visual Crossing](https://www.visualcrossing.com/weather-api)
- **Format**: `...`

### OpenWeather API Key (Optional)
- **Required**: No
- **Purpose**: Alternative weather data source
- **Get it from**: [OpenWeatherMap](https://openweathermap.org/api)

## 🔧 Configuration Options

### Environment Settings
```bash
ENVIRONMENT=development  # Options: development, production, testing
DEBUG=true              # Enable debug mode
```

### API Server Settings
```bash
API_HOST=0.0.0.0       # Server host
API_PORT=8000          # Server port
API_BASE_URL=http://localhost:8000  # Base URL for API calls
```

### RAG System Settings
```bash
MAX_CHUNKS=15000       # Maximum chunks to process
EMBEDDING_BATCH_SIZE=64 # Batch size for embeddings
CHUNK_SIZE=150         # Size of text chunks
OVERLAP_SIZE=30        # Overlap between chunks
```

### Cache Settings
```bash
WEATHER_CACHE_TTL=3600     # Weather cache TTL (seconds)
GEOCODE_CACHE_TTL=86400    # Geocode cache TTL (seconds)
SOIL_CACHE_TTL=86400       # Soil data cache TTL (seconds)
```

### UI Settings
```bash
UI_TIMEOUT=30          # API timeout (seconds)
UI_RETRY_ATTEMPTS=3    # Number of retry attempts
UI_RETRY_DELAY=1       # Delay between retries (seconds)
ENABLE_MOCK_API=false  # Enable mock API for testing
```

### Voice Settings
```bash
VOICE_CONTINUOUS=false     # Continuous voice recognition
VOICE_INTERIM_RESULTS=false # Show interim results
VOICE_TIMEOUT=10           # Voice timeout (seconds)
VOICE_PHRASE_TIME_LIMIT=30 # Max phrase duration (seconds)
```

## 🔒 Security Best Practices

### 1. Never Commit .env Files
```bash
# Add to .gitignore
.env
.env.local
.env.production
```

### 2. Use Different Keys for Different Environments
```bash
# Development
OPENAI_API_KEY=sk-proj-dev-...

# Production
OPENAI_API_KEY=sk-proj-prod-...
```

### 3. Rotate API Keys Regularly
- Set reminders to rotate keys every 90 days
- Monitor API usage for unusual activity
- Use environment-specific keys

## 🧪 Testing Your Configuration

### 1. Validate Required Keys
```python
from src.config import config

# Check for missing keys
missing_keys = config.validate_required_keys()
if missing_keys:
    print(f"Missing required API keys: {missing_keys}")
else:
    print("✅ All required API keys are configured")
```

### 2. Test API Connections
```python
# Test OpenAI
import openai
openai.api_key = config.OPENAI_API_KEY

# Test Google Translate
# Test Weather API
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Module Import Errors
```bash
# Make sure you're in the project root
cd /path/to/your/project

# Install dependencies
pip install -r requirements.txt
```

#### 2. API Key Not Found
```bash
# Check if .env file exists
ls -la .env

# Verify key format
echo $OPENAI_API_KEY
```

#### 3. Permission Denied
```bash
# Check file permissions
chmod 600 .env
```

### Environment Variable Debugging
```python
import os
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

# Check specific variables
print(f"OpenAI Key: {os.getenv('OPENAI_API_KEY', 'NOT SET')}")
print(f"Google Key: {os.getenv('GOOGLE_TRANSLATE_API_KEY', 'NOT SET')}")
```

## 📚 Additional Resources

- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [Environment Variables Best Practices](https://12factor.net/config)
- [API Security Guidelines](https://owasp.org/www-project-api-security/)

## ✅ Verification Checklist

- [ ] `.env` file created
- [ ] All required API keys added
- [ ] Environment variables loaded correctly
- [ ] No hardcoded values in code
- [ ] Configuration validation passes
- [ ] API connections working
- [ ] Tests passing
- [ ] `.env` added to `.gitignore`

## 🆘 Need Help?

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all API keys are correct
3. Ensure `.env` file is in the project root
4. Check file permissions
5. Restart your application after making changes

---

**Remember**: Keep your API keys secure and never share them publicly!
