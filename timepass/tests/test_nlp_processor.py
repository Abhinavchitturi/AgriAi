"""
Tests for Member A's NLP Processor
Tests all components: language detection, translation, intent extraction, and entity extraction
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.nlp_processor import NLPProcessor
from src.language_detection import LanguageDetector
from src.translation_service import TranslationService
from src.intent_extraction import IntentExtractor
from src.entity_extraction import EntityExtractor

class TestLanguageDetector:
    """Test language detection functionality"""
    
    def setup_method(self):
        self.detector = LanguageDetector()
    
    def test_detect_hindi(self):
        """Test Hindi language detection"""
        text = "पिछले हफ्ते बारिश हुई क्या?"
        lang_code, confidence = self.detector.detect_language(text)
        
        assert lang_code == 'hi'
        assert confidence > 0.5
        assert self.detector.get_language_name(lang_code) == 'Hindi'
    
    def test_detect_english(self):
        """Test English language detection"""
        text = "Did it rain last week?"
        lang_code, confidence = self.detector.detect_language(text)
        
        assert lang_code == 'en'
        assert confidence > 0.5
        assert self.detector.get_language_name(lang_code) == 'English'
    
    def test_detect_spanish(self):
        """Test Spanish language detection"""
        text = "¿Cuál es el clima hoy?"
        lang_code, confidence = self.detector.detect_language(text)
        
        assert lang_code == 'es'
        assert confidence > 0.5
        assert self.detector.get_language_name(lang_code) == 'Spanish'
    
    def test_empty_text(self):
        """Test empty text handling"""
        lang_code, confidence = self.detector.detect_language("")
        
        assert lang_code == 'en'
        assert confidence == 0.0
    
    def test_supported_languages(self):
        """Test supported languages"""
        assert self.detector.is_supported_language('hi')
        assert self.detector.is_supported_language('en')
        assert not self.detector.is_supported_language('xx')

class TestTranslationService:
    """Test translation functionality"""
    
    def setup_method(self):
        self.translator = TranslationService()
    
    @patch('src.translation_service.Translator')
    def test_translate_hindi_to_english(self, mock_translator):
        """Test Hindi to English translation"""
        # Mock the translation
        mock_translation = Mock()
        mock_translation.text = "Did it rain last week?"
        mock_translator.return_value.translate.return_value = mock_translation
        
        result = self.translator.translate_to_english("पिछले हफ्ते बारिश हुई क्या?", "hi")
        
        assert result['translated_text'] == "Did it rain last week?"
        assert result['source_language'] == 'hi'
        assert result['target_language'] == 'en'
        assert result['method'] == 'google_translate'
    
    def test_translate_english_to_english(self):
        """Test English to English (no translation needed)"""
        result = self.translator.translate_to_english("Did it rain last week?", "en")
        
        assert result['translated_text'] == "Did it rain last week?"
        assert result['source_language'] == 'en'
        assert result['target_language'] == 'en'
        assert result['method'] == 'no_translation_needed'
        assert result['confidence'] == 1.0
    
    def test_empty_text_translation(self):
        """Test empty text translation"""
        result = self.translator.translate_to_english("", "hi")
        
        assert result['translated_text'] == ""
        assert result['method'] == 'empty_text'
        assert result['confidence'] == 0.0

class TestIntentExtractor:
    """Test intent extraction functionality"""
    
    def setup_method(self):
        self.extractor = IntentExtractor()
    
    def test_weather_intent(self):
        """Test weather intent detection"""
        result = self.extractor.extract_intent("Did it rain last week?")
        
        assert result['intent'] == 'weather_check'
        assert result['confidence'] > 0.0
        assert result['method'] in ['pattern_matching', 'ml_classification', 'fallback']
    
    def test_crop_intent(self):
        """Test crop intent detection"""
        result = self.extractor.extract_intent("When should I plant corn?")
        
        assert result['intent'] == 'crop_info'
        assert result['confidence'] > 0.0
    
    def test_soil_intent(self):
        """Test soil intent detection"""
        result = self.extractor.extract_intent("What's the soil pH?")
        
        assert result['intent'] == 'soil_analysis'
        assert result['confidence'] > 0.0
    
    def test_empty_text_intent(self):
        """Test empty text intent extraction"""
        result = self.extractor.extract_intent("")
        
        assert result['intent'] == 'unknown'
        assert result['confidence'] == 0.0
        assert result['method'] == 'empty_text'

class TestEntityExtractor:
    """Test entity extraction functionality"""
    
    def setup_method(self):
        self.extractor = EntityExtractor()
    
    def test_time_entities(self):
        """Test time entity extraction"""
        result = self.extractor.extract_entities("Did it rain last week?")
        
        assert 'time' in result['entities']
        assert 'last week' in result['entities']['time']
        assert result['confidence'] > 0.0
    
    def test_crop_entities(self):
        """Test crop entity extraction"""
        result = self.extractor.extract_entities("When should I plant corn?")
        
        assert 'crop' in result['entities']
        assert 'corn' in result['entities']['crop']
        assert result['confidence'] > 0.0
    
    def test_location_entities(self):
        """Test location entity extraction"""
        result = self.extractor.extract_entities("Did it rain last week in Delhi?")
        
        assert 'location' in result['entities']
        assert result['confidence'] > 0.0
    
    def test_empty_text_entities(self):
        """Test empty text entity extraction"""
        result = self.extractor.extract_entities("")
        
        assert result['entities'] == {}
        assert result['confidence'] == 0.0
        assert result['method'] == 'empty_text'

class TestNLPProcessor:
    """Test the main NLP processor"""
    
    def setup_method(self):
        self.processor = NLPProcessor()
    
    def test_complete_pipeline_hindi(self):
        """Test complete pipeline with Hindi input"""
        query = "पिछले हफ्ते बारिश हुई क्या?"
        result = self.processor.process_query(query)
        
        # Check basic structure
        assert 'original_query' in result
        assert 'cleaned_query' in result
        assert 'language_detection' in result
        assert 'translation' in result
        assert 'intent_extraction' in result
        assert 'entity_extraction' in result
        assert 'processing_metadata' in result
        
        # Check language detection
        assert result['language_detection']['detected_language'] == 'hi'
        assert result['language_detection']['language_name'] == 'Hindi'
        
        # Check translation
        assert result['translation']['translated_text'] != query
        assert result['translation']['target_language'] == 'en'
        
        # Check intent
        assert result['intent_extraction']['intent'] == 'weather_check'
        
        # Check entities
        assert 'time' in result['entity_extraction']['entities']
        
        # Check processing time
        assert result['processing_metadata']['processing_time_seconds'] > 0
    
    def test_complete_pipeline_english(self):
        """Test complete pipeline with English input"""
        query = "Did it rain last week?"
        result = self.processor.process_query(query)
        
        # Check basic structure
        assert 'original_query' in result
        assert 'cleaned_query' in result
        
        # Check language detection
        assert result['language_detection']['detected_language'] == 'en'
        
        # Check translation (should be same as original)
        assert result['translation']['translated_text'] == query
        
        # Check intent
        assert result['intent_extraction']['intent'] == 'weather_check'
        
        # Check entities
        assert 'time' in result['entity_extraction']['entities']
    
    def test_empty_query(self):
        """Test empty query handling"""
        result = self.processor.process_query("")
        
        assert result['cleaned_query'] == ""
        assert 'error' in result or result['language_detection']['detected_language'] == 'en'
    
    def test_validation(self):
        """Test result validation"""
        query = "Did it rain last week?"
        result = self.processor.process_query(query)
        validation = self.processor.validate_processing(result)
        
        assert validation['is_valid'] == True
        assert isinstance(validation['warnings'], list)
        assert isinstance(validation['errors'], list)
    
    def test_processing_summary(self):
        """Test processing summary generation"""
        query = "Did it rain last week?"
        result = self.processor.process_query(query)
        summary = self.processor.get_processing_summary(result)
        
        assert summary['status'] == 'success'
        assert summary['original_language'] == 'English'
        assert summary['translated_text'] == query
        assert summary['detected_intent'] == 'weather_check'
        assert summary['processing_time'] > 0

class TestIntegration:
    """Integration tests for the complete system"""
    
    def setup_method(self):
        self.processor = NLPProcessor()
    
    def test_multilingual_queries(self):
        """Test processing queries in multiple languages"""
        test_cases = [
            ("पिछले हफ्ते बारिश हुई क्या?", "weather_check"),  # Hindi
            ("Did it rain last week?", "weather_check"),  # English
            ("¿Llovió la semana pasada?", "weather_check"),  # Spanish
            ("When should I plant corn?", "crop_info"),  # English
            ("What's the soil pH?", "soil_analysis"),  # English
        ]
        
        for query, expected_intent in test_cases:
            result = self.processor.process_query(query)
            
            # Basic validation
            assert result['original_query'] == query
            assert result['cleaned_query'] != ""
            assert result['intent_extraction']['intent'] == expected_intent
            assert result['processing_metadata']['processing_time_seconds'] > 0
    
    def test_error_handling(self):
        """Test error handling in the pipeline"""
        # Test with None input
        result = self.processor.process_query(None)
        assert 'error' in result
        
        # Test with very long input
        long_query = "test " * 1000
        result = self.processor.process_query(long_query)
        assert 'error' not in result or result['cleaned_query'] != ""

if __name__ == "__main__":
    pytest.main([__file__]) 