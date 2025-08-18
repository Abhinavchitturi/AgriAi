"""
Language Detection Module for Member A
Handles detection of user query language and provides language information
"""

import langdetect
from langdetect import DetectorFactory
from typing import Dict, Optional, Tuple
import logging

# Set seed for consistent language detection
DetectorFactory.seed = 0

class LanguageDetector:
    """Detects the language of user queries"""
    
    def __init__(self):
        self.supported_languages = {
            'hi': 'Hindi',
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'ru': 'Russian'
        }
        self.logger = logging.getLogger(__name__)
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the input text
        
        Args:
            text (str): Input text to detect language
            
        Returns:
            Tuple[str, float]: (language_code, confidence_score)
        """
        try:
            if not text or not text.strip():
                return 'en', 0.0
            
            # First try script-based detection for Indian languages
            script_detection = self._detect_by_script(text)
            if script_detection[0] != 'unknown':
                self.logger.info(f"Script-based detection: {script_detection[0]} with confidence: {script_detection[1]:.3f}")
                return script_detection
            
            # Fallback to langdetect
            detections = langdetect.detect_langs(text)
            
            if not detections:
                return 'en', 0.0
            
            # Get the most likely language
            primary_lang = detections[0]
            language_code = primary_lang.lang
            confidence = primary_lang.prob
            
            # If langdetect gives low confidence and detects English for non-Latin script, 
            # it's probably wrong - try script detection again
            if language_code == 'en' and confidence < 0.7 and self._contains_non_latin_script(text):
                script_detection = self._detect_by_script(text)
                if script_detection[0] != 'unknown':
                    self.logger.info(f"Overriding low-confidence English detection with script-based: {script_detection[0]}")
                    return script_detection
            
            # Keep the detected language even if not in our supported list
            if language_code not in self.supported_languages:
                self.logger.info(f"Detected unsupported language: {language_code}, keeping as detected")
            
            self.logger.info(f"Detected language: {language_code} with confidence: {confidence:.3f}")
            return language_code, confidence
            
        except Exception as e:
            self.logger.error(f"Error in language detection: {e}")
            # Try script-based detection as fallback
            script_detection = self._detect_by_script(text)
            if script_detection[0] != 'unknown':
                return script_detection
            return 'en', 0.0
    
    def get_language_name(self, language_code: str) -> str:
        """
        Get the full language name from language code
        
        Args:
            language_code (str): Language code (e.g., 'hi', 'en')
            
        Returns:
            str: Full language name
        """
        # Return the language name if supported, otherwise return the code
        if language_code in self.supported_languages:
            return self.supported_languages[language_code]
        else:
            # For unsupported languages, try to get a readable name
            # You can expand this mapping as needed
            extended_names = {
                'te': 'Telugu',
                'ta': 'Tamil', 
                'kn': 'Kannada',
                'mr': 'Marathi',
                'bn': 'Bengali',
                'gu': 'Gujarati',
                'ml': 'Malayalam',
                'pa': 'Punjabi',
                'or': 'Odia',
                'as': 'Assamese'
            }
            return extended_names.get(language_code, language_code.upper())
    
    def is_supported_language(self, language_code: str) -> bool:
        """
        Check if a language code is supported
        
        Args:
            language_code (str): Language code to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return language_code in self.supported_languages
    
    def _detect_by_script(self, text: str) -> Tuple[str, float]:
        """
        Detect language based on Unicode script ranges
        This is more reliable for Indian languages than langdetect
        """
        if not text:
            return 'unknown', 0.0
        
        # Count characters in different script ranges
        script_counts = {
            'devanagari': 0,  # Hindi, Marathi, Sanskrit
            'telugu': 0,      # Telugu
            'tamil': 0,       # Tamil
            'kannada': 0,     # Kannada
            'malayalam': 0,   # Malayalam
            'gujarati': 0,    # Gujarati
            'bengali': 0,     # Bengali, Assamese
            'gurmukhi': 0,    # Punjabi
            'oriya': 0,       # Odia
            'latin': 0,       # English, European languages
            'arabic': 0,      # Arabic
            'cyrillic': 0,    # Russian
        }
        
        for char in text:
            code_point = ord(char)
            
            # Telugu: U+0C00–U+0C7F
            if 0x0C00 <= code_point <= 0x0C7F:
                script_counts['telugu'] += 1
            # Tamil: U+0B80–U+0BFF
            elif 0x0B80 <= code_point <= 0x0BFF:
                script_counts['tamil'] += 1
            # Devanagari: U+0900–U+097F (Hindi, Marathi)
            elif 0x0900 <= code_point <= 0x097F:
                script_counts['devanagari'] += 1
            # Kannada: U+0C80–U+0CFF
            elif 0x0C80 <= code_point <= 0x0CFF:
                script_counts['kannada'] += 1
            # Malayalam: U+0D00–U+0D7F
            elif 0x0D00 <= code_point <= 0x0D7F:
                script_counts['malayalam'] += 1
            # Gujarati: U+0A80–U+0AFF
            elif 0x0A80 <= code_point <= 0x0AFF:
                script_counts['gujarati'] += 1
            # Bengali/Assamese: U+0980–U+09FF
            elif 0x0980 <= code_point <= 0x09FF:
                script_counts['bengali'] += 1
            # Gurmukhi (Punjabi): U+0A00–U+0A7F
            elif 0x0A00 <= code_point <= 0x0A7F:
                script_counts['gurmukhi'] += 1
            # Oriya (Odia): U+0B00–U+0B7F
            elif 0x0B00 <= code_point <= 0x0B7F:
                script_counts['oriya'] += 1
            # Arabic: U+0600–U+06FF
            elif 0x0600 <= code_point <= 0x06FF:
                script_counts['arabic'] += 1
            # Cyrillic: U+0400–U+04FF
            elif 0x0400 <= code_point <= 0x04FF:
                script_counts['cyrillic'] += 1
            # Latin: U+0000–U+007F, U+0080–U+00FF
            elif (0x0000 <= code_point <= 0x007F) or (0x0080 <= code_point <= 0x00FF):
                if char.isalpha():
                    script_counts['latin'] += 1
        
        # Find the dominant script
        total_chars = sum(script_counts.values())
        if total_chars == 0:
            return 'unknown', 0.0
        
        # Map scripts to language codes
        script_to_lang = {
            'telugu': 'te',
            'tamil': 'ta', 
            'devanagari': 'hi',  # Default to Hindi for Devanagari
            'kannada': 'kn',
            'malayalam': 'ml',
            'gujarati': 'gu',
            'bengali': 'bn',
            'gurmukhi': 'pa',
            'oriya': 'or',
            'arabic': 'ar',
            'cyrillic': 'ru',
            'latin': 'en'
        }
        
        # Find the script with the highest count
        dominant_script = max(script_counts, key=script_counts.get)
        dominant_count = script_counts[dominant_script]
        
        # Calculate confidence based on proportion of characters in dominant script
        confidence = dominant_count / total_chars
        
        # Only return a result if we have reasonable confidence
        if confidence >= 0.3 and dominant_count >= 3:  # At least 30% and 3 characters
            return script_to_lang[dominant_script], confidence
        
        return 'unknown', 0.0
    
    def _contains_non_latin_script(self, text: str) -> bool:
        """Check if text contains non-Latin script characters"""
        for char in text:
            code_point = ord(char)
            # Check for various non-Latin scripts
            if (0x0900 <= code_point <= 0x097F or  # Devanagari
                0x0980 <= code_point <= 0x09FF or  # Bengali
                0x0A00 <= code_point <= 0x0A7F or  # Gurmukhi
                0x0A80 <= code_point <= 0x0AFF or  # Gujarati
                0x0B00 <= code_point <= 0x0B7F or  # Oriya
                0x0B80 <= code_point <= 0x0BFF or  # Tamil
                0x0C00 <= code_point <= 0x0C7F or  # Telugu
                0x0C80 <= code_point <= 0x0CFF or  # Kannada
                0x0D00 <= code_point <= 0x0D7F or  # Malayalam
                0x0400 <= code_point <= 0x04FF or  # Cyrillic
                0x0600 <= code_point <= 0x06FF):   # Arabic
                return True
        return False

# Example usage and testing
if __name__ == "__main__":
    detector = LanguageDetector()
    
    # Test cases
    test_queries = [
        "पिछले हफ्ते बारिश हुई क्या?",  # Hindi
        "Did it rain last week?",  # English
        "¿Llovió la semana pasada?",  # Spanish
        "Il a plu la semaine dernière?",  # French
    ]
    
    for query in test_queries:
        lang_code, confidence = detector.detect_language(query)
        lang_name = detector.get_language_name(lang_code)
        print(f"Query: {query}")
        print(f"Detected: {lang_name} ({lang_code}) - Confidence: {confidence:.3f}")
        print("-" * 50) 