"""
Main NLP Processor for Member A
Orchestrates language detection, translation, intent extraction, and entity extraction
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .language_detection import LanguageDetector
from .translation_service import TranslationService
from .intent_extraction import IntentExtractor
from .entity_extraction import EntityExtractor
from .weather_service import WeatherService

class NLPProcessor:
    """Main processor for Member A's NLP + Language Layer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.language_detector = LanguageDetector()
        self.translation_service = TranslationService()
        self.intent_extractor = IntentExtractor()
        self.entity_extractor = EntityExtractor()
        self.weather_service = WeatherService()
        
        self.logger.info("NLP Processor initialized with all components")
    
    def process_query(self, user_query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user query through the complete NLP pipeline
        
        Args:
            user_query (str): Original user query
            location (Optional[str]): User's location for context-specific processing
            
        Returns:
            Dict[str, Any]: Complete processing result
        """
        try:
            start_time = datetime.now()
            
            # Step 1: Detect Language
            self.logger.info("Step 1: Language Detection")
            lang_code, lang_confidence = self.language_detector.detect_language(user_query)
            lang_name = self.language_detector.get_language_name(lang_code)
            
            # Step 2: Translate to English
            self.logger.info("Step 2: Translation")
            translation_result = self.translation_service.translate_to_english(user_query, lang_code)
            
            # Display translation results in terminal for confirmation
            print(f"\n{'='*60}")
            print(f"🌐 TRANSLATION CONFIRMATION")
            print(f"{'='*60}")
            print(f"Original Query: {user_query}")
            print(f"Detected Language: {lang_name} ({lang_code})")
            print(f"Translated Text: {translation_result['translated_text']}")
            print(f"Translation Confidence: {translation_result.get('confidence', 'N/A')}")
            print(f"{'='*60}")
            print(f"✅ Translation completed. Processing continues...")
            print(f"{'='*60}\n")
            
            # Step 3: Extract Intent
            self.logger.info("Step 3: Intent Extraction")
            intent_result = self.intent_extractor.extract_intent(translation_result['translated_text'])
            
            # Step 4: Extract Entities
            self.logger.info("Step 4: Entity Extraction")
            entity_result = self.entity_extractor.extract_entities(translation_result['translated_text'])
            
            # Step 5: Weather Processing (always show weather if location is provided)
            self.logger.info("Step 5: Weather Processing")
            print(f"🔍 Processing weather for location: {location}")
            weather_result = self._process_weather_query(translation_result['translated_text'], entity_result['entities'], location)
            print(f"🌤️ Weather result: {weather_result.get('is_weather_query', False)}")
            
            # Step 6: Create cleaned query for downstream processing
            cleaned_query = self._create_cleaned_query(
                translation_result['translated_text'],
                intent_result['intent'],
                entity_result['entities']
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Compile final result
            result = {
                'original_query': user_query,
                'cleaned_query': cleaned_query,
                'language_detection': {
                    'detected_language': lang_code,
                    'language_name': lang_name,
                    'confidence': lang_confidence
                },
                'translation': translation_result,
                'intent_extraction': intent_result,
                'entity_extraction': entity_result,
                'weather_information': weather_result,
                'processing_metadata': {
                    'processing_time_seconds': processing_time,
                    'timestamp': datetime.now().isoformat(),
                    'pipeline_version': '1.0.0'
                }
            }
            
            self.logger.info(f"Query processing completed in {processing_time:.3f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in query processing: {e}")
            return {
                'original_query': user_query,
                'cleaned_query': user_query,
                'error': str(e),
                'processing_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error'
                },
                'language_detection': {
                    'detected_language': 'unknown',
                    'language_name': 'Unknown',
                    'confidence': 0.0
                },
                'translation': {
                    'translated_text': user_query,
                    'source_language': 'unknown',
                    'target_language': 'en',
                    'confidence': 0.0,
                    'method': 'error_fallback'
                },
                'intent_extraction': {
                    'intent': 'general_question',
                    'confidence': 0.0,
                    'method': 'error_fallback'
                },
                'entity_extraction': {
                    'entities': {},
                    'method': 'error_fallback'
                }
            }
    
    def _create_cleaned_query(self, translated_text: str, intent: str, entities: Dict[str, Any]) -> str:
        """
        Create a cleaned query for downstream processing
        
        Args:
            translated_text (str): Translated English text
            intent (str): Extracted intent
            entities (Dict[str, Any]): Extracted entities
            
        Returns:
            str: Cleaned query for Member B
        """
        # Start with the translated text
        cleaned_query = translated_text
        
        # Add intent context if available
        if intent and intent != 'unknown':
            cleaned_query = f"[INTENT: {intent}] {cleaned_query}"
        
        # Add key entities if available
        entity_context = []
        if entities:
            for entity_type, entity_list in entities.items():
                if entity_list:
                    entity_context.append(f"{entity_type}: {', '.join(entity_list)}")
        
        if entity_context:
            cleaned_query = f"[ENTITIES: {'; '.join(entity_context)}] {cleaned_query}"
        
        return cleaned_query
    
    def _is_agricultural_query(self, text: str) -> bool:
        """Check if the query is related to agriculture"""
        agricultural_keywords = [
            'crop', 'harvest', 'plant', 'seed', 'agriculture', 'farming', 'yield',
            'fertilizer', 'pest', 'soil', 'irrigation', 'cultivation', 'grow',
            'farm', 'farmer', 'field', 'rice', 'wheat', 'corn', 'tomato',
            'vegetable', 'fruit', 'organic', 'pesticide', 'herbicide'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in agricultural_keywords)
    
    def _calculate_weather_confidence(self, weather_data: Dict[str, Any]) -> float:
        """Calculate confidence score for weather data quality"""
        confidence = 0.0
        
        # Check if all essential weather fields are present
        essential_fields = ['temperature', 'humidity', 'wind_speed', 'description']
        present_fields = sum(1 for field in essential_fields if weather_data.get(field) is not None)
        field_completeness = present_fields / len(essential_fields)
        
        # Check data quality (reasonable ranges)
        temp_quality = 0.0
        if weather_data.get('temperature') is not None:
            temp = weather_data['temperature']
            if -50 <= temp <= 60:  # Reasonable temperature range
                temp_quality = 1.0
            elif -60 <= temp <= 70:  # Extended range
                temp_quality = 0.8
            else:
                temp_quality = 0.3
        
        humidity_quality = 0.0
        if weather_data.get('humidity') is not None:
            hum = weather_data['humidity']
            if 0 <= hum <= 100:  # Valid humidity range
                humidity_quality = 1.0
            else:
                humidity_quality = 0.5
        
        wind_quality = 0.0
        if weather_data.get('wind_speed') is not None:
            wind = weather_data['wind_speed']
            if 0 <= wind <= 50:  # Reasonable wind speed range
                wind_quality = 1.0
            elif 0 <= wind <= 100:  # Extended range
                wind_quality = 0.8
            else:
                wind_quality = 0.4
        
        # Calculate overall confidence
        confidence = (field_completeness * 0.4 + 
                     temp_quality * 0.2 + 
                     humidity_quality * 0.2 + 
                     wind_quality * 0.2)
        
        # Bonus for having multiple data sources
        if weather_data.get('source') and '+' in weather_data['source']:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _is_agricultural_query(self, query: str) -> bool:
        """
        Check if query is agricultural in nature
        
        Args:
            query (str): Query text
            
        Returns:
            bool: True if agricultural query
        """
        agricultural_keywords = [
            'crop', 'seed', 'plant', 'harvest', 'grow', 'agriculture',
            'suitable', 'variety', 'soil', 'moisture', 'farming', 'farm',
            'planting', 'growing', 'season', 'cultivation', 'yield', 'production'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in agricultural_keywords)
    
    def _process_weather_query(self, translated_text: str, entities: Dict[str, Any], user_location: Optional[str] = None) -> Dict[str, Any]:
        """
        Process weather-related queries and extract weather information
        
        Args:
            translated_text (str): Translated English text
            entities (Dict[str, Any]): Extracted entities
            user_location (Optional[str]): User's provided location
            
        Returns:
            Dict[str, Any]: Weather processing result
        """
        try:
            print(f"🌍 Weather processing - User location: {user_location}")
            print(f"🌍 Weather processing - Query: {translated_text}")
            
            # Always show weather if location is provided or if it's an agricultural query
            should_fetch_weather = (
                user_location or  # Location provided
                self.weather_service.is_weather_query(translated_text) or  # Weather query
                self._is_agricultural_query(translated_text)  # Agricultural query
            )
            
            if not should_fetch_weather:
                print(f"❌ Skipping weather - no location, not weather query, not agricultural")
                return {
                    'is_weather_query': False,
                    'weather_data': None,
                    'message': 'Not a weather-related query and no location provided'
                }
            
            # Extract location from query or entities
            location = None
            
            # Priority 1: Use user-provided location if available
            if user_location:
                location = user_location
                self.logger.info(f"Using user-provided location: {location}")
            # Priority 2: Try to get location from entities
            elif 'location' in entities and entities['location']:
                location = entities['location'][0]  # Take the first location found
            elif 'city' in entities and entities['city']:
                location = entities['city'][0]
            elif 'place' in entities and entities['place']:
                location = entities['place'][0]
            # Priority 3: Try to extract from query text
            elif self.weather_service.extract_location_from_query(translated_text):
                location = self.weather_service.extract_location_from_query(translated_text)
            # Priority 4: Use a default location only for weather/agricultural queries
            else:
                # Only default to a location if this appears to be a weather or agricultural query
                if (self.weather_service.is_weather_query(translated_text) or 
                    self._is_agricultural_query(translated_text)):
                    location = "Mumbai"  # Default location for weather/agricultural queries
                    self.logger.info(f"No location found in weather/agricultural query, using default: {location}")
                else:
                    location = None
                    self.logger.info(f"No location found and not a weather/agricultural query, skipping weather data")
            
            # Get weather information with timeline-based data retrieval (only if location is available)
            if location:
                weather_data = self.weather_service.get_weather_with_timeline(location, translated_text)
            else:
                weather_data = {"error": "No location available for weather query"}
            
            # Display weather results in terminal
            print(f"\n{'='*60}")
            print(f"🌤️  WEATHER INFORMATION")
            print(f"{'='*60}")
            print(f"Location: {location}")
            if 'error' not in weather_data:
                print(f"Temperature: {weather_data['temperature']}°C")
                print(f"Feels Like: {weather_data['feels_like']}°C")
                print(f"Humidity: {weather_data['humidity']}")
                print(f"Description: {weather_data['description']}")
                print(f"Wind Speed: {weather_data['wind_speed']} m/s")
                print(f"Source: {weather_data['source']}")
                
                # Display timeline information if available
                if 'timeline_info' in weather_data:
                    timeline = weather_data['timeline_info']
                    print(f"Timeline: {timeline['description']}")
                    print(f"Data Points: {timeline['data_points']} days")
                
                # Calculate and display weather confidence
                weather_confidence = self._calculate_weather_confidence(weather_data)
                print(f"Weather Confidence: {weather_confidence:.1%}")
            else:
                print(f"Error: {weather_data['error']}")
            print(f"{'='*60}")
            
            # Mark as weather query if location is provided or if it's a weather-related query
            is_weather_query = bool(user_location) or self.weather_service.is_weather_query(translated_text)
            
            return {
                'is_weather_query': is_weather_query,
                'location': location,
                'weather_data': weather_data,
                'timeline_info': weather_data.get('timeline_info', {}),
                'message': 'Weather information retrieved successfully' if 'error' not in weather_data else weather_data['error']
            }
            
        except Exception as e:
            self.logger.error(f"Error in weather processing: {e}")
            return {
                'is_weather_query': True,
                'weather_data': None,
                'error': str(e),
                'message': f'Error processing weather query: {str(e)}'
            }
    
    def get_processing_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the processing results
        
        Args:
            result (Dict[str, Any]): Full processing result
            
        Returns:
            Dict[str, Any]: Processing summary
        """
        if 'error' in result:
            return {
                'status': 'error',
                'error': result['error']
            }
        
        return {
            'status': 'success',
            'original_language': result['language_detection']['language_name'],
            'translated_text': result['translation']['translated_text'],
            'detected_intent': result['intent_extraction']['intent'],
            'intent_confidence': result['intent_extraction']['confidence'],
            'extracted_entities': result['entity_extraction']['entities'],
            'processing_time': result['processing_metadata']['processing_time_seconds']
        }
    
    def validate_processing(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the processing results
        
        Args:
            result (Dict[str, Any]): Processing result
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        if 'error' in result:
            validation['is_valid'] = False
            validation['errors'].append(result['error'])
            return validation
        
        # Check translation quality
        if result['translation']['confidence'] < 0.5:
            validation['warnings'].append("Low translation confidence")
        
        # Check intent confidence
        if result['intent_extraction']['confidence'] < 0.3:
            validation['warnings'].append("Low intent detection confidence")
        
        # Check if essential components are present
        if not result['cleaned_query']:
            validation['is_valid'] = False
            validation['errors'].append("No cleaned query generated")
        
        if not result['intent_extraction']['intent']:
            validation['warnings'].append("No intent detected")
        
        return validation

# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    processor = NLPProcessor()
    
    # Test cases
    test_queries = [
        "पिछले हफ्ते बारिश हुई क्या?",  # Hindi
        "Did it rain last week?",  # English
        "¿Cuál es el clima hoy?",  # Spanish
        "When should I plant corn?",  # English
        "What's the soil pH for tomatoes?",  # English
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Processing: {query}")
        print(f"{'='*60}")
        
        result = processor.process_query(query)
        summary = processor.get_processing_summary(result)
        validation = processor.validate_processing(result)
        
        print(f"Summary: {json.dumps(summary, indent=2)}")
        print(f"Validation: {json.dumps(validation, indent=2)}")
        
        if validation['warnings']:
            print(f"Warnings: {validation['warnings']}")
        if validation['errors']:
            print(f"Errors: {validation['errors']}") 