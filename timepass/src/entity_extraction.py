"""
Entity Extraction Module for Member A
Extracts structured entities from user queries
"""

import re
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import spacy
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

class EntityExtractor:
    """Extracts entities from user queries"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Define entity patterns
        self.entity_patterns = {
            'time': {
                'patterns': [
                    r'\b(last week|this week|next week)\b',
                    r'\b(last month|this month|next month)\b',
                    r'\b(last year|this year|next year)\b',
                    r'\b(yesterday|today|tomorrow)\b',
                    r'\b(\d{1,2} days ago|\d{1,2} weeks ago|\d{1,2} months ago)\b',
                    r'\b(in \d{1,2} days|in \d{1,2} weeks|in \d{1,2} months)\b',
                    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                    r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
                ]
            },
            'location': {
                'patterns': [
                    r'\b(in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(city|town|village|district|state)\b'
                ]
            },
            'crop': {
                'keywords': [
                    'corn', 'wheat', 'rice', 'soybeans', 'cotton', 'sugarcane',
                    'tomatoes', 'potatoes', 'onions', 'carrots', 'lettuce',
                    'apples', 'oranges', 'bananas', 'grapes', 'strawberries'
                ],
                'patterns': [
                    r'\b(corn|maize|wheat|rice|soybeans|cotton|sugarcane)\b',
                    r'\b(tomatoes|potatoes|onions|carrots|lettuce)\b',
                    r'\b(apples|oranges|bananas|grapes|strawberries)\b'
                ]
            },
            'weather_condition': {
                'keywords': ['rain', 'sunny', 'cloudy', 'hot', 'cold', 'humid', 'dry'],
                'patterns': [
                    r'\b(rain|raining|rainy|drizzle|storm)\b',
                    r'\b(sun|sunny|clear|bright)\b',
                    r'\b(cloud|cloudy|overcast)\b',
                    r'\b(hot|warm|cold|cool|freezing)\b',
                    r'\b(humid|dry|wet|moist)\b'
                ]
            },
            'soil_type': {
                'keywords': ['clay', 'sandy', 'loamy', 'silt', 'organic'],
                'patterns': [
                    r'\b(clay|sandy|loamy|silt|organic)\s+(soil|dirt)\b',
                    r'\b(soil|dirt)\s+(clay|sandy|loamy|silt|organic)\b'
                ]
            },
            'pest_type': {
                'keywords': ['aphids', 'beetles', 'worms', 'mites', 'fungus'],
                'patterns': [
                    r'\b(aphids|beetles|worms|mites|fungus|mold)\b',
                    r'\b(insects|bugs|pests)\b'
                ]
            },
            'measurement': {
                'patterns': [
                    r'\b(\d+(?:\.\d+)?)\s*(celsius|fahrenheit|degrees|cm|inches|mm)\b',
                    r'\b(\d+(?:\.\d+)?)\s*(kg|pounds|lbs|tons)\b',
                    r'\b(\d+(?:\.\d+)?)\s*(acres|hectares|sq\s*ft)\b'
                ]
            }
        }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from the given text
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, Any]: Extracted entities and metadata
        """
        try:
            if not text or not text.strip():
                return {
                    'entities': {},
                    'confidence': 0.0,
                    'method': 'empty_text'
                }
            
            # Method 1: Pattern matching
            pattern_entities = self._pattern_matching(text)
            
            # Method 2: spaCy NER
            spacy_entities = self._spacy_ner(text)
            
            # Method 3: Custom entity extraction
            custom_entities = self._custom_extraction(text)
            
            # Combine all entities
            all_entities = {}
            
            # Merge pattern entities
            for entity_type, entities in pattern_entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = []
                all_entities[entity_type].extend(entities)
            
            # Merge spaCy entities
            for entity_type, entities in spacy_entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = []
                all_entities[entity_type].extend(entities)
            
            # Merge custom entities
            for entity_type, entities in custom_entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = []
                all_entities[entity_type].extend(entities)
            
            # Remove duplicates and calculate confidence
            cleaned_entities = {}
            total_entities = 0
            
            for entity_type, entities in all_entities.items():
                unique_entities = list(set(entities))
                cleaned_entities[entity_type] = unique_entities
                total_entities += len(unique_entities)
            
            confidence = min(total_entities / 10.0, 1.0)  # Normalize confidence
            
            return {
                'entities': cleaned_entities,
                'confidence': confidence,
                'method': 'combined_extraction',
                'pattern_entities': pattern_entities,
                'spacy_entities': spacy_entities,
                'custom_entities': custom_entities
            }
            
        except Exception as e:
            self.logger.error(f"Error in entity extraction: {e}")
            return {
                'entities': {},
                'confidence': 0.0,
                'method': 'error_fallback',
                'error': str(e)
            }
    
    def _pattern_matching(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        entities = {}
        text_lower = text.lower()
        
        for entity_type, config in self.entity_patterns.items():
            entity_list = []
            
            if 'patterns' in config:
                for pattern in config['patterns']:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    entity_list.extend(matches)
            
            if 'keywords' in config:
                for keyword in config['keywords']:
                    if keyword in text_lower:
                        entity_list.append(keyword)
            
            if entity_list:
                entities[entity_type] = entity_list
        
        return entities
    
    def _spacy_ner(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using spaCy NER"""
        entities = {}
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                entity_type = ent.label_.lower()
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].append(ent.text)
        
        except Exception as e:
            self.logger.error(f"spaCy NER error: {e}")
        
        return entities
    
    def _custom_extraction(self, text: str) -> Dict[str, List[str]]:
        """Custom entity extraction for domain-specific entities"""
        entities = {}
        
        # Extract time entities with more context
        time_entities = self._extract_time_entities(text)
        if time_entities:
            entities['time'] = time_entities
        
        # Extract location entities
        location_entities = self._extract_location_entities(text)
        if location_entities:
            entities['location'] = location_entities
        
        # Extract crop entities
        crop_entities = self._extract_crop_entities(text)
        if crop_entities:
            entities['crop'] = crop_entities
        
        return entities
    
    def _extract_time_entities(self, text: str) -> List[str]:
        """Extract time-related entities with normalization"""
        time_entities = []
        
        # Common time patterns
        time_patterns = [
            (r'\b(last week)\b', 'last_week'),
            (r'\b(this week)\b', 'this_week'),
            (r'\b(next week)\b', 'next_week'),
            (r'\b(yesterday)\b', 'yesterday'),
            (r'\b(today)\b', 'today'),
            (r'\b(tomorrow)\b', 'tomorrow'),
            (r'\b(\d{1,2})\s+days?\s+ago\b', 'days_ago'),
            (r'\b(\d{1,2})\s+weeks?\s+ago\b', 'weeks_ago'),
            (r'\b(\d{1,2})\s+months?\s+ago\b', 'months_ago'),
        ]
        
        for pattern, entity_type in time_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if entity_type == 'days_ago':
                    time_entities.append(f"{match} days ago")
                elif entity_type == 'weeks_ago':
                    time_entities.append(f"{match} weeks ago")
                elif entity_type == 'months_ago':
                    time_entities.append(f"{match} months ago")
                else:
                    time_entities.append(match)
        
        return time_entities
    
    def _extract_location_entities(self, text: str) -> List[str]:
        """Extract location entities"""
        location_entities = []
        
        # Location patterns
        location_patterns = [
            r'\b(in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(city|town|village|district|state)\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle tuple matches from regex groups
                    for group in match:
                        if group and group.strip():
                            location_entities.append(group.strip())
                else:
                    # Handle single string matches
                    if match and match.strip():
                        location_entities.append(match.strip())
        
        return location_entities
    
    def _extract_crop_entities(self, text: str) -> List[str]:
        """Extract crop-related entities"""
        crop_entities = []
        
        # Crop keywords
        crops = [
            'corn', 'wheat', 'rice', 'soybeans', 'cotton', 'sugarcane',
            'tomatoes', 'potatoes', 'onions', 'carrots', 'lettuce',
            'apples', 'oranges', 'bananas', 'grapes', 'strawberries'
        ]
        
        text_lower = text.lower()
        for crop in crops:
            if crop in text_lower:
                crop_entities.append(crop)
        
        return crop_entities

# Example usage and testing
if __name__ == "__main__":
    extractor = EntityExtractor()
    
    # Test cases
    test_queries = [
        "Did it rain last week in Delhi?",
        "What's the temperature today?",
        "When should I plant corn in my field?",
        "How much wheat can I harvest from 5 acres?",
        "Is the soil pH good for tomatoes?",
    ]
    
    for query in test_queries:
        result = extractor.extract_entities(query)
        print(f"Query: {query}")
        print(f"Entities: {result['entities']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Method: {result['method']}")
        print("-" * 50) 