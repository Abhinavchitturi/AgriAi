"""
FastAPI Application for Member A's NLP + Language Layer
Provides API endpoints for query processing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.nlp_processor import NLPProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import config

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    description="API for language detection, translation, intent extraction, and entity extraction",
    version=config.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Initialize NLP processor
nlp_processor = NLPProcessor()

# Pydantic models for request/response
class SimpleQueryRequest(BaseModel):
    query: str = Field(..., description="User query to process (any language)")
    language: Optional[str] = Field(None, description="Detected or selected language of the query")
    timestamp: Optional[str] = Field(None, description="Timestamp of the query")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context including location")

class QueryRequest(BaseModel):
    query: str = Field(..., description="User query to process")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")

class SimpleQueryResponse(BaseModel):
    query: str = Field(..., description="Original user query")
    language: str = Field(..., description="Detected language")
    translated_text: str = Field(..., description="Translated text in English")
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., description="Confidence score")
    entities: Dict[str, Any] = Field(..., description="Extracted entities")
    weather_data: Optional[Dict[str, Any]] = Field(None, description="Weather information if query is weather-related")
    timeline_info: Optional[Dict[str, Any]] = Field(None, description="Timeline information for weather data retrieval")
    rag_response: Optional[str] = Field(None, description="Direct RAG response for ultra-fast mode")
    processing_mode: Optional[str] = Field(None, description="Processing mode used (ultra_fast_direct, rag, etc.)")

class QueryResponse(BaseModel):
    status: str = Field(..., description="Processing status")
    original_query: str = Field(..., description="Original user query")
    cleaned_query: str = Field(..., description="Cleaned query for downstream processing")
    language_detection: Dict[str, Any] = Field(..., description="Language detection results")
    translation: Dict[str, Any] = Field(..., description="Translation results")
    intent_extraction: Dict[str, Any] = Field(..., description="Intent extraction results")
    entity_extraction: Dict[str, Any] = Field(..., description="Entity extraction results")
    processing_metadata: Dict[str, Any] = Field(..., description="Processing metadata")
    validation: Dict[str, Any] = Field(..., description="Validation results")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    components: Dict[str, str] = Field(..., description="Component status")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Member A: NLP + Language Layer API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/query", response_model=SimpleQueryResponse)
async def process_simple_query(request: SimpleQueryRequest):
    """
    Simple endpoint to process any query in any language
    
    Just provide the query and get back:
    - Detected language
    - Translated text (in English)
    - Intent classification
    - Extracted entities
    """
    try:
        # Log the received query for debugging
        logger.info(f"Received query: {request.query}")
        logger.info(f"Query type: {type(request.query)}")
        logger.info(f"Query length: {len(request.query)}")
        
        # Extract location from context if available
        user_location = request.context.get('location') if request.context else None
        logger.info(f"User location: {user_location}")
        
        # Process the query through the NLP pipeline with location context
        result = nlp_processor.process_query(request.query, user_location=user_location)
        
        # Check if there was an error in processing
        if 'error' in result:
            logger.error(f"Processing error: {result['error']}")
            raise HTTPException(status_code=422, detail=f"Processing error: {result['error']}")
        
        # Extract the key information for simple response
        weather_info = result.get('weather_information', {})
        
        return SimpleQueryResponse(
            query=request.query,
            language=result.get('language_detection', {}).get('language_name', 'Unknown'),
            translated_text=result.get('translation', {}).get('translated_text', request.query),
            intent=result.get('intent_extraction', {}).get('intent', 'general_question'),
            confidence=result.get('intent_extraction', {}).get('confidence', 0.0),
            entities=result.get('entity_extraction', {}).get('entities', {}),
            weather_data=weather_info.get('weather_data', {}) if weather_info.get('weather_data') else None,
            timeline_info=weather_info.get('timeline_info', {}) if weather_info.get('timeline_info') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/query-raw")
async def process_query_raw(request: Request):
    """
    Raw endpoint to handle Unicode characters better
    """
    try:
        # Get raw JSON data
        body = await request.json()
        query = body.get('query', '')
        
        logger.info(f"Raw query received: {query}")
        
        # Process the query
        result = nlp_processor.process_query(query)
        
        # Return simple response
        return {
            "query": query,
            "language": result.get('language_detection', {}).get('language_name', 'Unknown'),
            "translated_text": result.get('translation', {}).get('translated_text', query),
            "intent": result.get('intent_extraction', {}).get('intent', 'general_question'),
            "confidence": result.get('intent_extraction', {}).get('confidence', 0.0),
            "entities": result.get('entity_extraction', {}).get('entities', {})
        }
        
    except Exception as e:
        logger.error(f"Raw endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test NLP processor components
        test_result = nlp_processor.process_query("test")
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            components={
                "language_detector": "healthy",
                "translation_service": "healthy",
                "intent_extractor": "healthy",
                "entity_extractor": "healthy",
                "nlp_processor": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/process", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the complete NLP pipeline
    
    This endpoint handles:
    1. Language detection
    2. Translation to English
    3. Intent extraction
    4. Entity extraction
    5. Query cleaning for downstream processing
    """
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Process the query
        result = nlp_processor.process_query(request.query)
        
        # Validate the result
        validation = nlp_processor.validate_processing(result)
        
        # Add validation to result
        result['validation'] = validation
        
        # Check if processing was successful
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Create response
        response = QueryResponse(**result)
        
        logger.info(f"Query processed successfully in {result['processing_metadata']['processing_time_seconds']:.3f} seconds")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/detect-language")
async def detect_language(request: QueryRequest):
    """Detect the language of a query"""
    try:
        lang_code, confidence = nlp_processor.language_detector.detect_language(request.query)
        lang_name = nlp_processor.language_detector.get_language_name(lang_code)
        
        return {
            "detected_language": lang_code,
            "language_name": lang_name,
            "confidence": confidence,
            "original_query": request.query
        }
    except Exception as e:
        logger.error(f"Error in language detection: {e}")
        raise HTTPException(status_code=500, detail=f"Language detection error: {str(e)}")

@app.post("/translate")
async def translate_query(request: QueryRequest):
    """Translate a query to English"""
    try:
        # First detect language
        lang_code, _ = nlp_processor.language_detector.detect_language(request.query)
        
        # Then translate
        translation_result = nlp_processor.translation_service.translate_to_english(request.query, lang_code)
        
        return {
            "original_query": request.query,
            "detected_language": lang_code,
            "translation": translation_result
        }
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

@app.post("/extract-intent")
async def extract_intent(request: QueryRequest):
    """Extract intent from a query"""
    try:
        intent_result = nlp_processor.intent_extractor.extract_intent(request.query)
        
        return {
            "original_query": request.query,
            "intent_extraction": intent_result
        }
    except Exception as e:
        logger.error(f"Error in intent extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Intent extraction error: {str(e)}")

@app.post("/extract-entities")
async def extract_entities(request: QueryRequest):
    """Extract entities from a query"""
    try:
        entity_result = nlp_processor.entity_extractor.extract_entities(request.query)
        
        return {
            "original_query": request.query,
            "entity_extraction": entity_result
        }
    except Exception as e:
        logger.error(f"Error in entity extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Entity extraction error: {str(e)}")

@app.post("/weather")
async def get_weather(request: QueryRequest):
    """Get weather information for a location mentioned in the query"""
    try:
        # First process the query to extract location and check if it's weather-related
        result = nlp_processor.process_query(request.query)
        
        weather_info = result.get('weather_information', {})
        
        if weather_info.get('is_weather_query', False):
            return {
                "original_query": request.query,
                "is_weather_query": True,
                "location": weather_info.get('location', 'Unknown'),
                "weather_data": weather_info.get('weather_data', {}),
                "message": weather_info.get('message', 'Weather information retrieved'),
                "processing_summary": nlp_processor.get_processing_summary(result)
            }
        else:
            return {
                "original_query": request.query,
                "is_weather_query": False,
                "message": "Query is not weather-related. Try asking about weather, temperature, or climate.",
                "suggestions": [
                    "What's the weather in Mumbai?",
                    "How hot is it in Delhi?",
                    "Is it raining in Bangalore?",
                    "Temperature in Chennai"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Weather processing error: {str(e)}")

@app.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "supported_languages": nlp_processor.language_detector.supported_languages,
        "total_languages": len(nlp_processor.language_detector.supported_languages)
    }

@app.get("/intent-types")
async def get_intent_types():
    """Get list of supported intent types"""
    return {
        "intent_types": list(nlp_processor.intent_extractor.intent_patterns.keys()),
        "total_intents": len(nlp_processor.intent_extractor.intent_patterns)
    }

@app.get("/entity-types")
async def get_entity_types():
    """Get list of supported entity types"""
    return {
        "entity_types": list(nlp_processor.entity_extractor.entity_patterns.keys()),
        "total_entity_types": len(nlp_processor.entity_extractor.entity_patterns)
    }

# Background task for processing queries asynchronously
async def process_query_background(query: str, user_id: Optional[str] = None):
    """Background task for processing queries"""
    try:
        result = nlp_processor.process_query(query)
        logger.info(f"Background processing completed for user {user_id}")
        return result
    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        return {"error": str(e)}

@app.post("/process-async")
async def process_query_async(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a query asynchronously"""
    try:
        # Add background task
        background_tasks.add_task(process_query_background, request.query, request.user_id)
        
        return {
            "status": "processing",
            "message": "Query submitted for background processing",
            "query": request.query,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error submitting background task: {e}")
        raise HTTPException(status_code=500, detail=f"Background processing error: {str(e)}")

@app.post("/query-rag")
async def process_query_with_rag(request: SimpleQueryRequest):
    """
    Enhanced endpoint that uses RAG system for better responses
    
    This endpoint:
    1. Processes the query through NLP pipeline
    2. Uses RAG system to find relevant information from agricultural data and weather
    3. Returns comprehensive answers with confidence scores
    """
    try:
        # Log the received query for debugging
        logger.info(f"RAG Query received: {request.query}")
        
        # Extract location from context if available
        location = None
        if request.context and 'location' in request.context:
            location = request.context['location']
        
        # Import RAG system
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from rag.current import process_rag_query, get_rag_status, add_weather_data_to_existing_index
        
        # Check if this is a weather-related query before fetching weather data
        weather_data = None
        
        # First, determine if this is actually a weather-related query
        is_weather_query = (
            location and (  # Only proceed if location is provided
                any(weather_word in request.query.lower() for weather_word in [
                    'weather', 'temperature', 'rain', 'humidity', 'wind', 'climate', 'forecast',
                    'hot', 'cold', 'sunny', 'cloudy', 'storm', 'precipitation', 'moisture'
                ]) or
                any(agri_word in request.query.lower() for agri_word in [
                    'crop', 'farm', 'agriculture', 'plant', 'seed', 'harvest', 'grow',
                    'soil', 'irrigation', 'cultivation', 'yield', 'suitable', 'productivity',
                    'farming', 'agricultural', 'production', 'improve', 'increase', 'better',
                    'tips', 'advice', 'techniques', 'methods', 'strategies'
                ])
            )
        )
        
        # Check if this is an agricultural query that needs special handling (even without location)
        is_agricultural_query = any(agri_word in request.query.lower() for agri_word in [
            'crop', 'farm', 'agriculture', 'plant', 'seed', 'harvest', 'grow',
            'soil', 'irrigation', 'cultivation', 'yield', 'suitable', 'productivity',
            'farming', 'agricultural', 'production', 'improve', 'increase', 'better',
            'tips', 'advice', 'techniques', 'methods', 'strategies'
        ])
        
        if is_weather_query:
            try:
                from src.weather_service import WeatherService
                weather_service = WeatherService()
                # Use timeline-based weather fetching for all queries
                weather_data = weather_service.get_weather_with_timeline(location, request.query)
                
                # Check if we should bypass RAG for maximum speed
                timeline_info = weather_data.get('timeline_info', {})
                processing_mode = timeline_info.get('mode', '')
                requested_days = timeline_info.get('requested_days', 0)
                
                # Check if this is a crop-specific query that should use RAG
                query_lower = request.query.lower()
                is_crop_specific_query = any(crop in query_lower for crop in [
                    'wheat', 'rice', 'corn', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane',
                    'maize', 'barley', 'oats', 'pulses', 'legumes', 'vegetables', 'fruits'
                ]) and any(word in query_lower for word in [
                    'when', 'suitable', 'grow', 'plant', 'cultivate', 'harvest', 'season',
                    'timing', 'conditions', 'requirements', 'best time', 'optimal'
                ])
                
                # ALL queries now go through RAG system - no bypassing
                print(f"🔄 All queries routed to RAG system for comprehensive responses")
                
                # No direct response generation - all queries go to RAG
                print(f"📚 Query '{request.query}' will be processed by RAG system")
                
                # Helper function to generate weather range information for RAG enhancement
                def generate_weather_range_info(location, weather_data, timeline_info):
                    """Generate weather range information for the detected timeline period"""
                    try:
                        timeline_desc = timeline_info.get('description', '120 days')
                        requested_days = timeline_info.get('requested_days', 120)
                        
                        if 'daily' in weather_data and weather_data['daily']:
                            daily_data = weather_data['daily']
                            if len(daily_data) > 0:
                                # Calculate ranges from daily data
                                temps = [day.get('temp', day.get('temp_c', 0)) for day in daily_data if day.get('temp') or day.get('temp_c')]
                                humidities = [day.get('humidity', 0) for day in daily_data if day.get('humidity')]
                                moistures = [day.get('moisture', 0) for day in daily_data if day.get('moisture')]
                                rainfalls = [day.get('precip_mm', day.get('precip', day.get('rainfall', 0))) for day in daily_data if day.get('precip_mm') or day.get('precip') or day.get('rainfall')]
                                
                                if temps:
                                    temp_range = f"Temperature ranging from {min(temps):.1f}°C to {max(temps):.1f}°C"
                                else:
                                    temp_range = f"Temperature: {weather_data.get('temperature', 'N/A')}°C"
                                    
                                if humidities:
                                    humidity_range = f"Humidity ranging from {min(humidities):.1f}% to {max(humidities):.1f}%"
                                else:
                                    humidity_range = f"Humidity: {weather_data.get('humidity', 'N/A')}%"
                                    
                                if moistures:
                                    moisture_range = f"Moisture ranging from {min(moistures):.1f}% to {max(moistures):.1f}%"
                                else:
                                    moisture_range = f"Moisture: {weather_data.get('moisture', 'N/A')}%"
                                    
                                if rainfalls:
                                    rainfall_range = f"Rainfall ranging from {min(rainfalls):.1f}mm to {max(rainfalls):.1f}mm"
                                else:
                                    rainfall_range = f"Rainfall: {weather_data.get('precipitation', 'N/A')}mm"
                                
                                return f"**Weather for {location} for {timeline_desc}:**\n{temp_range}, {humidity_range}, {moisture_range}, {rainfall_range}\n\n"
                        
                        # Fallback to current values
                        return f"**Weather for {location} for {timeline_desc}:**\nTemperature: {weather_data.get('temperature', 'N/A')}°C, Humidity: {weather_data.get('humidity', 'N/A')}%, Moisture: {weather_data.get('moisture', 'N/A')}%, Rainfall: {weather_data.get('precipitation', 'N/A')}mm\n\n"
                    except Exception as e:
                        # Fallback to current weather if range calculation fails
                        timeline_desc = timeline_info.get('description', '120 days')
                        return f"**Weather for {location} for {timeline_desc}:**\nTemperature: {weather_data.get('temperature', 'N/A')}°C, Humidity: {weather_data.get('humidity', 'N/A')}%, Moisture: {weather_data.get('moisture', 'N/A')}%, Rainfall: {weather_data.get('precipitation', 'N/A')}mm\n\n"
                
                print(f"✅ Timeline-based weather data fetched for {location}: {weather_data.get('temperature', 'N/A')}°C, {weather_data.get('humidity', 'N/A')}% humidity, {weather_data.get('moisture', 'N/A')}% moisture, {weather_data.get('wind_speed', 'N/A')} m/s wind")
                
                # Log timeline information
                if 'timeline_info' in weather_data:
                    timeline = weather_data['timeline_info']
                    print(f"📅 Timeline: {timeline.get('description', 'N/A')} ({timeline.get('data_points', 'N/A')} days)")
                else:
                    print(f"📅 Timeline: Default 120 days")
                    
            except Exception as e:
                print(f"⚠️ Could not fetch weather data: {e}")
                weather_data = {"error": f"Weather fetch failed: {str(e)}"}
        elif is_agricultural_query and not location:
            # Handle agricultural queries without location - provide general advice
            print(f"🌾 Agricultural query detected without location - providing general farming advice")
            
            # Analyze the query to determine response type
            query_lower = request.query.lower()
            
            # Check for yield improvement queries
            is_yield_improvement = any(phrase in query_lower for phrase in [
                'increase yield', 'improve yield', 'better yield', 'higher yield', 'maximize yield',
                'crop yield', 'farming tips', 'agricultural advice', 'farming techniques',
                'how to farm', 'farming methods', 'crop production', 'agricultural productivity'
            ])
            
            if is_yield_improvement:
                direct_response = """**🌾 General Yield Improvement Strategies (No Location Specified):**

**Soil Management:**
• **Soil Testing:** Regular soil testing for pH, NPK levels, and organic matter
• **Soil Health:** Maintain 3-5% organic matter content for optimal fertility
• **pH Balance:** Keep soil pH between 6.0-7.0 for most crops
• **Soil Structure:** Improve soil structure through proper tillage and organic amendments

**Water Management:**
• **Irrigation:** Use efficient irrigation systems (drip, sprinkler) based on crop needs
• **Soil Moisture:** Maintain optimal soil moisture levels (usually 60-80% field capacity)
• **Drainage:** Ensure proper drainage to prevent waterlogging
• **Water Conservation:** Implement rainwater harvesting and mulching

**Fertilization:**
• **Balanced NPK:** Apply fertilizers based on soil test results and crop requirements
• **Organic Matter:** Use compost, manure, and cover crops to improve soil fertility
• **Micronutrients:** Address micronutrient deficiencies (zinc, boron, iron, manganese)
• **Timing:** Apply fertilizers at the right growth stages for maximum efficiency

**Crop Management:**
• **Variety Selection:** Choose high-yielding, disease-resistant varieties adapted to your climate
• **Planting Density:** Optimize plant spacing for maximum light and nutrient access
• **Crop Rotation:** Practice crop rotation to prevent soil depletion and pest buildup
• **Intercropping:** Use intercropping systems for better resource utilization

**Pest & Disease Management:**
• **Integrated Pest Management (IPM):** Combine biological, cultural, and chemical controls
• **Monitoring:** Regular field scouting for early pest/disease detection
• **Prevention:** Use resistant varieties and cultural practices to prevent problems
• **Treatment:** Apply appropriate treatments only when necessary

**Technology & Innovation:**
• **Precision Agriculture:** Use GPS, sensors, and data analytics for optimal management
• **Modern Equipment:** Invest in efficient planting, harvesting, and processing equipment
• **Digital Tools:** Use apps and software for crop planning and monitoring
• **Research:** Stay updated with latest agricultural research and best practices

**Climate Adaptation:**
• **Weather Monitoring:** Track weather patterns and forecasts for better planning
• **Climate-Smart Practices:** Implement practices that work with your local climate
• **Seasonal Planning:** Adjust planting and management based on seasonal weather patterns
• **Risk Management:** Diversify crops and use insurance to manage climate risks

**📍 To get location-specific advice:** Please provide your location (city, state, or region) for personalized recommendations based on your local weather, soil, and climate conditions."""
                
                return SimpleQueryResponse(
                    query=request.query,
                    language='English',
                    translated_text=request.query,
                    intent="agricultural_advice_query",
                    confidence=0.95,
                    entities={"location": None, "timeline": "general"},
                    weather_data=None,
                    timeline_info=None,
                    rag_response=direct_response,
                    processing_mode="agricultural_advice_direct"
                )
        
        else:
            if location:
                print(f"🚫 Non-weather query detected - skipping weather data for location: {location}")
            else:
                print("⚠️ No location provided - weather data unavailable")
        
        # Process query through RAG system with weather data
        rag_result = process_rag_query(
            query=request.query, 
            location=location,
            weather_data=weather_data  # Always pass weather data (even if error)
        )
        
        # Ensure we have a valid answer
        if not rag_result or not rag_result.get('answer'):
            raise ValueError("RAG system returned empty or invalid result")
        
        # Add weather range information to RAG responses for agricultural queries
        if is_agricultural_query and location and weather_data and not weather_data.get('error'):
            try:
                # Generate weather range info for RAG responses
                weather_range_info = generate_weather_range_info(location, weather_data, timeline_info)
                
                # Prepend weather info to RAG answer
                enhanced_answer = f"{weather_range_info}{rag_result.get('answer', '')}"
                rag_result['answer'] = enhanced_answer
                print(f"🌾 Enhanced RAG response with weather context for agricultural query")
            except Exception as e:
                print(f"⚠️ Could not enhance RAG response with weather info: {e}")
        
        # Return clean RAG result without debugging info
        return {
            "answer": rag_result.get('answer', 'No answer generated'),
            "source": rag_result.get('source', 'RAG System'),
            "confidence": rag_result.get('confidence', 0.0),
            "error": False,
            "processing_mode": "RAG Enhanced",
            # Remove debugging fields - only include essential info
            "language": rag_result.get('detected_language', 'Unknown'),
            "location": location
        }
        
    except Exception as e:
        logger.error(f"Unexpected error processing RAG query: {e}")
        print(f"❌ RAG processing error: {e}")
        
        # Fallback to regular NLP processing
        try:
            print("🔄 Falling back to regular NLP processing...")
            if 'nlp_result' not in locals():
                nlp_result = nlp_processor.process_query(request.query, location=location)
            
            # Create fallback response
            translated_text = nlp_result.get('translation', {}).get('translated_text', request.query)
            language = nlp_result.get('language_detection', {}).get('language_name', 'Unknown')
            
            return {
                "answer": f"RAG system temporarily unavailable. Based on your query '{request.query}' (detected as {language}), I've processed it as: '{translated_text}'. For detailed agricultural advice, please try again in a moment.",
                "source": "Fallback NLP System",
                "confidence": 0.3,
                "error": True,
                "error_message": f"RAG Error: {str(e)}",
                "language": language,
                "intent": nlp_result.get('intent_extraction', {}).get('intent', 'general_question'),
                "entities": nlp_result.get('entity_extraction', {}).get('entities', {}),
                "processing_mode": "Fallback NLP"
            }
        except Exception as fallback_error:
            return {
                "answer": f"System temporarily unavailable: {str(e)}",
                "source": "System Error",
                "confidence": 0.0,
                "error": True,
                "error_message": str(fallback_error),
                "processing_mode": "Error"
            }

@app.get("/rag-status")
async def get_rag_system_status():
    """Get RAG system status"""
    try:
        import sys
        import os
        rag_path = os.path.join(os.path.dirname(__file__), '..', 'rag')
        if rag_path not in sys.path:
            sys.path.append(rag_path)
        
        from rag.current import get_rag_status
        return get_rag_status()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/refresh-weather")
async def refresh_weather_data():
    """Force refresh of weather data in RAG system"""
    try:
        import sys
        import os
        rag_path = os.path.join(os.path.dirname(__file__), '..', 'rag')
        if rag_path not in sys.path:
            sys.path.append(rag_path)
        
        from rag.current import refresh_weather_data
        return refresh_weather_data()
    except Exception as e:
        return {"status": "error", "message": f"Error refreshing weather data: {str(e)}"}

@app.post("/query-ui")
async def process_query_for_ui(request: SimpleQueryRequest):
    """
    UI-friendly endpoint that returns response format expected by Streamlit UI
    
    Returns:
    - answer: The translated text (what the UI expects)
    - source: Source information
    - confidence: Confidence score
    - language: Detected language
    - intent: Detected intent
    - entities: Extracted entities
    """
    try:
        # Log the received query for debugging
        logger.info(f"UI Query received: {request.query}")
        
        # Extract location from context if available
        location = None
        if request.context and 'location' in request.context:
            location = request.context['location']
        
        # Display query received in terminal
        print(f"\n{'='*60}")
        print(f"📝 NEW QUERY RECEIVED FROM UI")
        print(f"{'='*60}")
        print(f"Query: {request.query}")
        print(f"Location: {location or 'Not provided'}")
        print(f"User ID: {request.user_id or 'Anonymous'}")
        print(f"Timestamp: {request.timestamp or 'Not provided'}")
        print(f"{'='*60}")
        
        # Process the query through the NLP pipeline with location context
        result = nlp_processor.process_query(request.query, location=location)
        
        # Check if there was an error in processing
        if 'error' in result:
            logger.error(f"Processing error: {result['error']}")
            return {
                "answer": f"Error processing query: {result['error']}",
                "source": "System Error",
                "confidence": 0.0,
                "error": True,
                "language": "Unknown",
                "intent": "error",
                "entities": {}
            }
        
        # Extract the key information for UI response
        translated_text = result.get('translation', {}).get('translated_text', request.query)
        language = result.get('language_detection', {}).get('language_name', 'Unknown')
        intent = result.get('intent_extraction', {}).get('intent', 'general_question')
        confidence = result.get('intent_extraction', {}).get('confidence', 0.0)
        entities = result.get('entity_extraction', {}).get('entities', {})
        weather_info = result.get('weather_information', {})
        
        # Create a comprehensive answer based on the processing
        answer = f"Based on your query '{request.query}' (detected as {language}):\n\n"
        
        # Add location-specific information if available
        if location:
            answer += f"📍 Location: {location}\n\n"
        
        answer += f"Translated to English: '{translated_text}'\n\n"
        answer += f"Intent: {intent}\n"
        answer += f"Confidence: {confidence:.1%}\n"
        
        if entities:
            answer += f"\nExtracted entities: {entities}"
        
        # Add weather information if available
        if weather_info.get('is_weather_query', False) and weather_info.get('weather_data'):
            weather_data = weather_info['weather_data']
            if 'error' not in weather_data:
                answer += f"\n\n🌤️ Weather Information for {weather_info.get('location', 'Unknown')}:\n"
                answer += f"Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
                answer += f"Feels Like: {weather_data.get('feels_like', 'N/A')}°C\n"
                answer += f"Humidity: {weather_data.get('humidity', 'N/A')}\n"
                answer += f"Moisture: {weather_data.get('moisture', 'N/A')}\n"
                answer += f"Description: {weather_data.get('description', 'N/A')}\n"
                answer += f"Wind Speed: {weather_data.get('wind_speed', 'N/A')} m/s"
            else:
                answer += f"\n\n❌ Weather Error: {weather_data.get('error', 'Unknown error')}"
        elif weather_info.get('weather_data') and 'error' not in weather_info['weather_data']:
            # Always show weather if available, even for non-weather queries
            weather_data = weather_info['weather_data']
            answer += f"\n\n🌤️ Current Weather for {weather_info.get('location', 'Unknown')}:\n"
            answer += f"Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
            answer += f"Feels Like: {weather_data.get('feels_like', 'N/A')}°C\n"
            answer += f"Humidity: {weather_data.get('humidity', 'N/A')}\n"
            answer += f"Moisture: {weather_data.get('moisture', 'N/A')}\n"
            answer += f"Description: {weather_data.get('description', 'N/A')}\n"
            answer += f"Wind Speed: {weather_data.get('wind_speed', 'N/A')} m/s"
        
        # Display completion message in terminal
        print(f"✅ Processing completed successfully!")
        print(f"📤 Sending response to UI...")
        print(f"{'='*60}\n")
        
        return {
            "answer": answer,
            "source": "AgriAI NLP Processor",
            "confidence": confidence,
            "error": False,
            "language": language,
            "intent": intent,
            "entities": entities,
            "translated_text": translated_text,
            "original_query": request.query,
            "weather_data": weather_info.get('weather_data', {}),
            "is_weather_query": weather_info.get('is_weather_query', False),
            "location": weather_info.get('location', None)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error processing UI query: {e}")
        return {
            "answer": f"An unexpected error occurred: {str(e)}",
            "source": "System Error",
            "confidence": 0.0,
            "error": True,
            "language": "Unknown",
            "intent": "error",
            "entities": {}
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 