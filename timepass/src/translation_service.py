"""
Translation Service for Member A
Handles translation from detected language to English using Google Translate API
"""

import os
from typing import Optional, Dict, Any
import logging
import requests
from dotenv import load_dotenv

# Import centralized configuration
from .config import config

# Google Translate API configuration
GOOGLE_TRANSLATE_API_KEY = config.GOOGLE_TRANSLATE_API_KEY
GOOGLE_TRANSLATE_AVAILABLE = bool(GOOGLE_TRANSLATE_API_KEY)

class TranslationService:
    """Handles translation from various languages to English using Google Translate API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Google Translate API key
        self.google_api_key = GOOGLE_TRANSLATE_API_KEY
        
        # Check if Google Translate API is available
        self.use_google = bool(self.google_api_key)
        
        if not self.use_google:
            self.logger.warning("Google Translate API key not configured - translation will not work")
    
    def translate_to_english(self, text: str, source_lang: str) -> Dict[str, Any]:
        """
        Translate text from source language to English using Google Translate API
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code
            
        Returns:
            Dict[str, Any]: Translation result with translated text and metadata
        """
        try:
            if source_lang == 'en':
                return {
                    'translated_text': text,
                    'source_language': source_lang,
                    'target_language': 'en',
                    'confidence': 1.0,
                    'method': 'no_translation_needed'
                }
            
            if not text or not text.strip():
                return {
                    'translated_text': '',
                    'source_language': source_lang,
                    'target_language': 'en',
                    'confidence': 0.0,
                    'method': 'empty_text'
                }
            
            # Use Google Translate API (most reliable)
            if self.use_google:
                result = self._translate_with_google_api(text, source_lang)
                if result:
                    return result
            
            # If Google Translate API is not available, return original text
            self.logger.warning("Google Translate API key not configured - translation not available")
            return {
                'translated_text': text,
                'source_language': source_lang,
                'target_language': 'en',
                'confidence': 0.0,
                'method': 'google_api_not_configured',
                'error': 'Google Translate API key not configured'
            }
            
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return {
                'translated_text': text,
                'source_language': source_lang,
                'target_language': 'en',
                'confidence': 0.0,
                'method': 'error_fallback',
                'error': str(e)
            }
    
    def _translate_with_google_api(self, text: str, source_lang: str) -> Dict[str, Any]:
        """Translate using official Google Translate API"""
        try:
            if not self.google_api_key:
                self.logger.warning("Google Translate API key not configured")
                return None
            
            # Google Translate API endpoint
            url = "https://translation.googleapis.com/language/translate/v2"
            
            # Map our language codes to Google's format
            lang_mapping = {
                'te': 'te',    # Telugu
                'hi': 'hi',    # Hindi
                'ta': 'ta',    # Tamil
                'kn': 'kn',    # Kannada
                'mr': 'mr',    # Marathi
                'bn': 'bn',    # Bengali
                'gu': 'gu',    # Gujarati
                'ml': 'ml',    # Malayalam
                'pa': 'pa',    # Punjabi
                'or': 'or',    # Odia
                'as': 'as',    # Assamese
                'en': 'en',    # English
                'es': 'es',    # Spanish
                'fr': 'fr',    # French
                'de': 'de',    # German
                'ar': 'ar',    # Arabic
                'ru': 'ru'     # Russian
            }
            
            source_code = lang_mapping.get(source_lang, 'auto')
            
            params = {
                'key': self.google_api_key,
                'q': text,
                'source': source_code,
                'target': 'en',
                'format': 'text'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'translations' in data['data']:
                    translation = data['data']['translations'][0]
                    translated_text = translation.get('translatedText', '')
                    detected_source = translation.get('detectedSourceLanguage', source_lang)
                    
                    if translated_text and translated_text != text:
                        # Google Translate API is very reliable
                        confidence = 0.95
                        
                        self.logger.info(f"Google Translate API successful: '{text}' -> '{translated_text}'")
                
                return {
                            'translated_text': translated_text,
                            'source_language': detected_source,
                    'target_language': 'en',
                    'confidence': confidence,
                            'method': 'google_translate_api',
                    'original_text': text
                }
            else:
                self.logger.warning(f"Google Translate API HTTP error: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            self.logger.error(f"Google Translate API error: {e}")
            return None
    
    def detect_and_translate(self, text: str) -> Dict[str, Any]:
        """
        Detect language and translate to English in one step
        
        Args:
            text (str): Text to detect and translate
            
        Returns:
            Dict[str, Any]: Combined detection and translation result
        """
        from .language_detection import LanguageDetector
        
        detector = LanguageDetector()
        lang_code, confidence = detector.detect_language(text)
        
        translation_result = self.translate_to_english(text, lang_code)
        translation_result['detected_language'] = lang_code
        translation_result['detection_confidence'] = confidence
        
        return translation_result

# Example usage and testing
if __name__ == "__main__":
    translator = TranslationService()
    
    # Test cases
    test_queries = [
        "ఇప్పుడు వాతావరణం ఎలా ఉంది?",  # Telugu
        "पिछले हफ्ते बारिश हुई क्या?",  # Hindi
        "¿Cuál es el clima hoy?",  # Spanish
        "What's the weather like today?",  # English
    ]
    
    for query in test_queries:
        result = translator.detect_and_translate(query)
        print(f"Original: {query}")
        print(f"Translated: {result['translated_text']}")
        print(f"Detected Language: {result['detected_language']}")
        print(f"Method: {result['method']}")
        print("-" * 50) 