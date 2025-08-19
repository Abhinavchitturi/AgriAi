# 🌾 Agriculture AI Assistant

#IMPORTANT
First, run the backend, and then wait for sometime until it is finished, because it'll load upto 610 chunks before, which will help the application to run faster.
So first run the backend and wait for 5 mins, and then run the frontend and start giving the queries. (This is only happens sometimes)



## 🌾 Overview

The Agriculture AI Assistant is a sophisticated AI-powered system designed to help farmers, agricultural professionals, and enthusiasts with comprehensive agricultural knowledge, real-time weather data, and intelligent query processing. The system combines multiple AI technologies including:

- **Natural Language Processing (NLP)** for understanding queries in multiple languages
- **Retrieval-Augmented Generation (RAG)** for accurate agricultural knowledge retrieval
- **Real-time weather data integration** from multiple sources
- **Multilingual support** for Indian regional languages and international languages
- **Intelligent intent classification** and entity extraction

### 🎯 Target Users

- **Farmers** seeking agricultural advice and weather information
- **Agricultural professionals** needing technical information
- **Students** studying agriculture and related sciences
- **Researchers** analyzing agricultural data and trends
- **Extension workers** providing guidance to farmers

## 🚀 Features

### 🌍 **Multilingual Support**
- **Indian Languages**: Hindi, Telugu, Tamil, Kannada, Marathi, Bengali, Punjabi, Odia
- **Automatic language detection** and translation
- **Voice input support** for multiple languages

### 🌤️ **Weather Integration**
- **Real-time weather data** from Google Weather API
- **Historical weather patterns** from Visual Crossing Weather API
- **Soil moisture data** from NASA POWER API
- **Agricultural weather forecasting** with crop-specific recommendations
- **Timeline-based weather analysis** (7 days to 120 days)

### 🧠 **AI-Powered Intelligence**
- **OpenAI GPT-4o-mini** integration for natural language understanding
- **Sentence Transformers** for semantic search and embeddings
- **FAISS vector database** for efficient knowledge retrieval
- **Intent classification** for query understanding
- **Entity extraction** for location and crop identification

### 📚 **Knowledge Base**
- **Comprehensive agricultural datasets** including crop information, soil data, and farming practices
- **Dynamic knowledge retrieval** based on user queries
- **Context-aware responses** with relevant agricultural information
- **Source attribution** for all provided information

### 🔧 **Technical Features**
- **RESTful API** with FastAPI backend
- **Real-time processing** with caching mechanisms
- **Scalable architecture** supporting multiple concurrent users
- **Comprehensive logging** and monitoring
- **Environment-based configuration** management

## 🏗️ Architecture

### **System Components**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │   Mobile App    │    │   API Client    │
│   (Streamlit)   │    │   (React)       │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Backend       │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NLP           │    │   Weather       │    │   RAG           │
│   Processor     │    │   Service       │    │   System        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenAI        │    │   Google APIs   │    │   FAISS         │
│   GPT-4o-mini   │    │   (Weather,     │    │   Vector DB     │
│                  │    │    Translate)   │    │                  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Data Flow**

1. **User Input**: Query in any supported language
2. **Language Detection**: Automatic language identification
3. **Translation**: Convert to English for processing
4. **Intent Classification**: Determine query type and intent
5. **Entity Extraction**: Identify locations, crops, and parameters
6. **Weather Integration**: Fetch relevant weather data
7. **Knowledge Retrieval**: Search agricultural knowledge base
8. **Response Generation**: Create comprehensive answer using AI
9. **Translation Back**: Convert response to user's language

## 📦 Installation

### **Prerequisites**

- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **Git** for version control
- **Virtual environment** (recommended)
- **API keys** for required services

### **Step 1: Clone the Repository**

```bash
git clone <repository-url>
cd timepass
```

### **Step 2: Create Virtual Environment**

```bash
# Windows
python -m venv proj
proj\Scripts\activate

# macOS/Linux
python3 -m venv proj
source proj/bin/activate
```

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 4: Environment Setup**

```bash
# Copy environment template
Get-Content env_template.txt | Set-Content .env

# Or manually create .env file
cp env_template.txt .env
```

### **Step 5: Configure API Keys**

Edit the `.env` file with your actual API keys (see [API Keys Setup](#-api-keys-setup) section).

## ⚙️ Configuration

### **Environment Variables**

The system uses a comprehensive configuration system managed through environment variables:

#### **Core Settings**
```bash
ENVIRONMENT=development                    # development, production, testing
APP_NAME=Agriculture AI Assistant         # Application name
APP_VERSION=1.0.0                        # Version number
DEBUG=true                               # Debug mode
```

#### **Server Configuration**
```bash
API_HOST=0.0.0.0                        # Server host
API_PORT=8000                           # Server port
API_BASE_URL=http://localhost:8000      # Base URL for API calls
```

#### **AI Services**
```bash
OPENAI_API_KEY=your_openai_api_key      # OpenAI API key
OPENAI_MODEL=gpt-4o-mini                # OpenAI model to use
EMBEDDING_MODEL=all-MiniLM-L6-v2        # Sentence transformer model
LLM_TEMPERATURE=0.1                     # LLM temperature for responses
LLM_TEMPERATURE_ZERO=0.0                # LLM temperature for factual queries
```

#### **External APIs**
```bash
GOOGLE_TRANSLATE_API_KEY=your_key       # Google Translate API
GOOGLE_MAPS_API_KEY=your_key            # Google Maps/Weather API
VISUAL_CROSSING_API_KEY=your_key        # Visual Crossing Weather API
OPENWEATHER_API_KEY=your_key            # OpenWeather API (optional)
```

#### **System Configuration**
```bash
MAX_CHUNKS=15000                        # Maximum RAG chunks
EMBEDDING_BATCH_SIZE=64                 # Embedding batch size
CHUNK_SIZE=150                          # Text chunk size
OVERLAP_SIZE=30                         # Chunk overlap
WEATHER_CACHE_TTL=3600                  # Weather cache TTL (seconds)
```

### **Configuration File Structure**

The system automatically loads configuration from:
1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **Default values** (lowest priority)

## 🔑 API Keys Setup

### **Required API Keys**

#### **1. OpenAI API Key**
- **Purpose**: AI language processing and response generation
- **Get it from**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Format**: `sk-proj-...`
- **Cost**: Pay-per-use (typically $0.01-0.10 per query)

#### **2. Google Translate API Key**
- **Purpose**: Language translation services
- **Get it from**: [Google Cloud Console](https://console.cloud.google.com/)
- **Format**: `AIzaSy...`
- **Cost**: $20 per million characters

#### **3. Google Maps/Weather API Key**
- **Purpose**: Weather data and geocoding
- **Get it from**: [Google Cloud Console](https://console.cloud.google.com/)
- **Format**: `AIzaSy...`
- **Cost**: $5 per 1000 requests

#### **4. Visual Crossing Weather API Key**
- **Purpose**: Historical weather data and forecasting
- **Get it from**: [Visual Crossing](https://www.visualcrossing.com/weather-api)
- **Format**: `...`
- **Cost**: Free tier available, paid plans from $0.0001 per request

### **API Key Setup Steps**

1. **Create accounts** on required platforms
2. **Generate API keys** from respective dashboards
3. **Update `.env` file** with your keys
4. **Test configuration** using test scripts
5. **Set up billing** if required

### **Security Best Practices**

- ✅ **Never commit** `.env` files to version control
- ✅ **Use different keys** for development and production
- ✅ **Rotate keys regularly** (every 90 days)
- ✅ **Monitor API usage** for unusual activity
- ✅ **Set up rate limiting** and quotas

## 🌐 Usage

### **Starting the Application**

#### **Option 1: API Server Only**
```bash
# Start the FastAPI backend
python api/main.py
```

#### **Option 2: Full Application with UI**
```bash
# Terminal 1: Start API server
python api/main.py

# Terminal 2: Start Streamlit UI
streamlit run UI/app.py
```

#### **Option 3: Docker (if available)**
```bash
docker-compose up
```

### **Accessing the Application**

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **Health Check**: http://localhost:8000/health

### **Making Queries**

#### **Direct API Calls**
```bash
# Weather query
curl -X POST "http://localhost:8000/query-rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Mumbai?", "language": "en"}'

# Agricultural query
curl -X POST "http://localhost:8000/query-rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "How to grow tomatoes?", "language": "hi"}'
```

#### **Through Web UI**
1. Open http://localhost:8501 in your browser
2. Select your preferred language
3. Type or speak your question
4. Get comprehensive agricultural and weather information

### **Supported Query Types**

#### **Weather Queries**
- Current weather conditions
- Weather forecasts (daily, weekly)
- Agricultural weather analysis
- Soil moisture and temperature
- Rainfall predictions

#### **Agricultural Queries**
- Crop cultivation techniques
- Pest and disease management
- Soil fertility and fertilization
- Irrigation methods
- Harvesting and storage

#### **Combined Queries**
- Weather-based crop recommendations
- Seasonal farming advice
- Location-specific agricultural guidance
- Climate-adaptive farming practices

## 📚 API Documentation

### **Core Endpoints**

#### **POST /query-rag**
Main endpoint for processing agricultural and weather queries.

**Request Body:**
```json
{
  "query": "string",           // User query in any language
  "language": "string",        // Language code (optional, auto-detected)
  "context": {                 // Additional context (optional)
    "location": "string",      // Location for weather data
    "user_id": "string"       // User identifier
  }
}
```

**Response:**
```json
{
  "answer": "string",          // AI-generated response
  "confidence": 0.95,          // Confidence score (0-1)
  "source": "string",          // Information source
  "weather_data": {            // Weather information (if applicable)
    "temperature": 25.5,
    "humidity": 65,
    "description": "Partly cloudy"
  },
  "rag_info": {                // RAG system information
    "relevant_chunks": 5,
    "total_chunks_searched": 1500
  }
}
```

#### **GET /health**
Health check endpoint for monitoring system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "nlp": "operational",
    "weather": "operational",
    "rag": "operational"
  }
}
```

#### **GET /rag-status**
Get status of the RAG knowledge system.

**Response:**
```json
{
  "status": "ready",
  "total_chunks": 1500,
  "last_updated": "2024-01-15T10:30:00Z",
  "weather_locations": ["Mumbai", "Delhi", "Bangalore"]
}
```

### **Error Handling**

The API returns appropriate HTTP status codes and error messages:

- **200**: Success
- **400**: Bad request (invalid input)
- **401**: Unauthorized (invalid API key)
- **429**: Rate limited
- **500**: Internal server error

### **Rate Limiting**

- **Default limit**: 100 requests per minute per IP
- **Weather API calls**: 10 per minute per location
- **RAG queries**: 50 per minute per user

## 🧪 Testing

### **Running Tests**

#### **Configuration Tests**
```bash
# Test environment configuration
python test_config.py

# Test API key validation
python -c "from src.config import config; print(config.validate_required_keys())"
```

#### **API Tests**
```bash
# Test API endpoints
python -c "
import requests
response = requests.get('http://localhost:8000/health')
print(f'Health check: {response.status_code}')
"
```

#### **Integration Tests**
```bash
# Test complete flow
python test_complete_flow.py

# Test RAG integration
python test_rag_integration.py
```

### **Test Coverage**

The test suite covers:
- ✅ Configuration loading and validation
- ✅ API endpoint functionality
- ✅ Language detection and translation
- ✅ Weather data integration
- ✅ RAG system performance
- ✅ Error handling and edge cases

### **Performance Testing**

```bash
# Load testing with multiple concurrent users
python -c "
import asyncio
import aiohttp
import time

async def test_performance():
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        tasks = []
        for i in range(10):
            task = session.post('http://localhost:8000/query-rag', 
                              json={'query': f'Test query {i}', 'language': 'en'})
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        print(f'Processed 10 requests in {end_time - start_time:.2f} seconds')

asyncio.run(test_performance())
"
```

## 🔧 Development

### **Development Environment Setup**

1. **Clone the repository**
2. **Create virtual environment**
3. **Install development dependencies**
4. **Set up pre-commit hooks**
5. **Configure IDE settings**

### **Code Structure**

```
timepass/
├── api/                    # FastAPI backend
│   ├── main.py            # Main API server
│   └── models/            # Pydantic models
├── src/                    # Core source code
│   ├── config.py          # Configuration management
│   ├── nlp_processor.py   # Main NLP processor
│   ├── language_detection.py  # Language detection
│   ├── translation_service.py # Translation service
│   ├── intent_extraction.py   # Intent classification
│   ├── entity_extraction.py   # Entity extraction
│   ├── weather_service.py     # Weather integration
│   ├── metrics_service.py     # Performance metrics
│   └── timeline_extractor.py  # Timeline processing
├── rag/                    # RAG system
│   ├── current.py         # Main RAG implementation
│   └── data/              # Knowledge base data
├── UI/                     # User interface
│   ├── app.py             # Streamlit application
│   ├── config.py          # UI configuration
│   └── utils.py           # UI utilities
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

### **Adding New Features**

#### **1. New Language Support**
1. Add language code to `SUPPORTED_LANGUAGES`
2. Update translation mappings
3. Add language-specific UI text
4. Test with sample queries

#### **2. New Weather Data Source**
1. Create new service class
2. Implement standard interface
3. Add configuration options
4. Update weather service factory

#### **3. New Agricultural Knowledge**
1. Prepare data in CSV/Excel format
2. Run data preprocessing
3. Rebuild FAISS index
4. Test knowledge retrieval

### **Debugging**

#### **Enable Debug Mode**
```bash
# Set in .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

#### **View Logs**
```bash
# Check application logs
tail -f logs/agriculture_ai.log

# Check API logs
python api/main.py --log-level debug
```

#### **Common Issues**
- **API key errors**: Check `.env` file and API key validity
- **Import errors**: Verify virtual environment and dependencies
- **Memory issues**: Check RAG chunk sizes and batch processing
- **Rate limiting**: Monitor API usage and implement backoff

## 📁 Project Structure

### **Detailed Directory Layout**

```
timepass/
├── 📁 api/                          # Backend API server
│   ├── 📄 main.py                  # FastAPI application entry point
│   ├── 📁 models/                  # Data models and schemas
│   │   └── 📄 intent_classifier.pkl # Trained intent classification model
│   └── 📄 __init__.py
├── 📁 src/                          # Core application logic
│   ├── 📄 __init__.py
│   ├── 📄 config.py                # Centralized configuration management
│   ├── 📄 nlp_processor.py         # Main NLP processing pipeline
│   ├── 📄 language_detection.py    # Language detection service
│   ├── 📄 translation_service.py   # Multi-language translation
│   ├── 📄 intent_extraction.py     # Intent classification
│   ├── 📄 entity_extraction.py     # Named entity recognition
│   ├── 📄 weather_service.py       # Weather data integration
│   ├── 📄 metrics_service.py       # Performance monitoring
│   └── 📄 timeline_extractor.py    # Timeline data processing
├── 📁 rag/                          # RAG knowledge system
│   ├── 📄 current.py               # Main RAG implementation
│   ├── 📄 data_core.csv            # Core agricultural dataset
│   ├── 📄 embeddings.npy           # Pre-computed embeddings
│   ├── 📄 faiss_index.idx          # FAISS vector index
│   ├── 📄 faiss_chunks.csv         # Text chunks for retrieval
│   ├── 📄 faiss_meta.json          # Index metadata
│   └── 📁 models/                  # RAG-specific models
├── 📁 UI/                           # User interface components
│   ├── 📄 app.py                   # Streamlit web application
│   ├── 📄 config.py                # UI configuration
│   ├── 📄 api_client.py            # API client for UI
│   ├── 📄 utils.py                 # UI utility functions
│   ├── 📄 deploy.py                # Deployment configuration
│   ├── 📄 Dockerfile               # Docker container definition
│   ├── 📄 requirements.txt         # UI-specific dependencies
│   └── 📄 README.md                # UI-specific documentation
├── 📁 tests/                        # Test suite
│   └── 📄 test_nlp_processor.py    # NLP processor tests
├── 📁 models/                       # Shared models and data
│   └── 📄 intent_classifier.pkl    # Intent classification model
├── 📄 requirements.txt              # Main Python dependencies
├── 📄 req.txt                       # Alternative requirements file
├── 📄 .env                          # Environment variables (not in git)
├── 📄 env_template.txt              # Environment template
├── 📄 .gitignore                    # Git ignore rules
├── 📄 setup_env.py                  # Environment setup script
├── 📄 test_config.py                # Configuration testing script
├── 📄 initialize_rag.py             # RAG system initialization
├── 📄 ENVIRONMENT_SETUP.md          # Environment setup guide
├── 📄 RAG_INTEGRATION_GUIDE.md      # RAG system documentation
├── 📄 COMPLETE_INTEGRATION_GUIDE.md # Complete system guide
├── 📄 WEATHER_FEATURE.md            # Weather feature documentation
└── 📄 README.md                     # This comprehensive guide
```

### **Key Files Explanation**

#### **Configuration Files**
- **`.env`**: Contains all API keys and configuration (not committed to git)
- **`env_template.txt`**: Template for creating `.env` file
- **`src/config.py`**: Centralized configuration management system

#### **Core Application Files**
- **`src/nlp_processor.py`**: Main NLP processing pipeline
- **`src/weather_service.py`**: Weather data integration service
- **`rag/current.py`**: RAG knowledge retrieval system

#### **API and UI Files**
- **`api/main.py`**: FastAPI backend server
- **`UI/app.py`**: Streamlit web interface
- **`UI/api_client.py`**: API client for UI

#### **Data and Models**
- **`rag/faiss_index.idx`**: Vector database for semantic search
- **`rag/embeddings.npy`**: Pre-computed text embeddings
- **`models/intent_classifier.pkl`**: Trained intent classification model

## 🤝 Contributing

### **How to Contribute**

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation**
6. **Submit a pull request**

### **Development Guidelines**

- **Code style**: Follow PEP 8 guidelines
- **Documentation**: Add docstrings for all functions
- **Testing**: Maintain >80% test coverage
- **Type hints**: Use Python type hints
- **Error handling**: Implement proper error handling

### **Code Review Process**

1. **Automated checks** (linting, testing)
2. **Peer review** by maintainers
3. **Integration testing** on staging
4. **Deployment** to production

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### **License Terms**

- ✅ **Commercial use** allowed
- ✅ **Modification** allowed
- ✅ **Distribution** allowed
- ✅ **Private use** allowed
- ❌ **No warranty** provided
- ❌ **No liability** for damages

## 🆘 Troubleshooting

### **Common Issues and Solutions**

#### **1. API Key Errors**

**Problem**: `401 Unauthorized` or `Invalid API key` errors

**Solutions**:
```bash
# Check API key in .env file
Get-Content .env | Select-String "OPENAI_API_KEY"

# Verify key format
python -c "from src.config import config; print(f'Key length: {len(config.OPENAI_API_KEY)}')"

# Test API key validity
python -c "
import openai
openai.api_key = 'your-api-key-here'
try:
    response = openai.ChatCompletion.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': 'Hello'}]
    )
    print('✅ API key is valid')
except Exception as e:
    print(f'❌ API key error: {e}')
"
```

#### **2. Import Errors**

**Problem**: `ModuleNotFoundError` or import failures

**Solutions**:
```bash
# Activate virtual environment
proj\Scripts\activate  # Windows
source proj/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### **3. Memory Issues**

**Problem**: Out of memory errors during RAG processing

**Solutions**:
```bash
# Reduce chunk sizes in .env
MAX_CHUNKS=5000
EMBEDDING_BATCH_SIZE=32

# Use CPU-only mode
export CUDA_VISIBLE_DEVICES=""

# Monitor memory usage
python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

#### **4. Weather API Rate Limiting**

**Problem**: `429 Too Many Requests` errors

**Solutions**:
```bash
# Implement exponential backoff
# Reduce concurrent requests
# Use caching more aggressively

# Check current rate limits
python -c "
import time
import requests
response = requests.get('http://localhost:8000/rag-status')
print(f'API status: {response.json()}')
"
```

#### **5. RAG System Not Working**

**Problem**: No relevant results or empty responses

**Solutions**:
```bash
# Rebuild FAISS index
python initialize_rag.py

# Check index status
python -c "
from rag.current import get_rag_status
status = get_rag_status()
print(f'RAG status: {status}')
"

# Verify data files exist
ls -la rag/*.csv rag/*.idx
```

### **Performance Optimization**

#### **1. Response Time Optimization**
```bash
# Enable caching
WEATHER_CACHE_TTL=7200  # 2 hours
GEOCODE_CACHE_TTL=86400  # 24 hours

# Reduce embedding batch size
EMBEDDING_BATCH_SIZE=32

# Use smaller models
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### **2. Memory Optimization**
```bash
# Limit concurrent users
MAX_CONCURRENT_USERS=10

# Reduce chunk overlap
OVERLAP_SIZE=20

# Enable garbage collection
import gc
gc.collect()
```

#### **3. API Rate Limiting**
```bash
# Implement request queuing
# Use multiple API keys
# Implement exponential backoff
```

### **Monitoring and Logging**

#### **1. Enable Detailed Logging**
```bash
# Set in .env file
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

#### **2. Monitor System Health**
```bash
# Health check endpoint
curl http://localhost:8000/health

# RAG status
curl http://localhost:8000/rag-status

# Performance metrics
python -c "
from src.metrics_service import get_performance_metrics
metrics = get_performance_metrics()
print(f'Performance: {metrics}')
"
```

#### **3. Error Tracking**
```bash
# Check error logs
tail -f logs/agriculture_ai.log | grep ERROR

# Monitor API errors
python -c "
import requests
try:
    response = requests.get('http://localhost:8000/nonexistent')
    print(f'Response: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')
"
```

## 📞 Support and Contact

### **Getting Help**

- **Documentation**: Check this README and other guide files
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers directly

### **Community Resources**

- **GitHub Repository**: [Project Repository](https://github.com/yourusername/timepass)
- **Documentation**: [Project Wiki](https://github.com/yourusername/timepass/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/timepass/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/timepass/discussions)

### **Maintainers**

- **Lead Developer**: [Your Name](mailto:your.email@example.com)
- **Contributors**: See [Contributors](https://github.com/yourusername/timepass/graphs/contributors) page

---

## 🎉 **Quick Start Summary**

1. **Clone repository**: `git clone <url> && cd timepass`
2. **Setup environment**: `python -m venv proj && proj\Scripts\activate`
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Configure API keys**: Edit `.env` file with your keys
5. **Initialize RAG**: `python initialize_rag.py`
6. **Start server**: `python api/main.py`
7. **Access application**: http://localhost:8000

**Happy Farming with AI! 🌾🤖**

---

*This README is comprehensive and covers all aspects of the Agriculture AI Assistant project. For specific implementation details, refer to the individual module documentation and source code.* 
