"""
Intent Extraction Module for Member A
Determines the user's intention from the translated query
"""

import re
from typing import Dict, List, Tuple, Any
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import os

class IntentExtractor:
    """Extracts intent from user queries"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define intent patterns and keywords
        self.intent_patterns = {
            'weather_check': {
                'keywords': ['weather', 'rain', 'sunny', 'cloudy', 'temperature', 'forecast', 'climate', 'hot', 'cold', 'humid', 'dry', 'wind', 'storm', 'drizzle', 'precipitation', 'mausam', 'barish', 'garmi', 'thand', 'pani'],
                'patterns': [
                    r'\b(weather|climate|forecast|mausam)\b',
                    r'\b(rain|raining|rainy|barish)\b',
                    r'\b(sun|sunny|clear|garmi)\b',
                    r'\b(temperature|temp|hot|cold|thand)\b',
                    r'\b(humid|dry|pani)\b',
                    r'\b(wind|storm|drizzle|precipitation)\b',
                    r'\b(how.*weather|what.*weather|weather.*like)\b'
                ]
            },
            'crop_info': {
                'keywords': ['crop', 'harvest', 'plant', 'seed', 'agriculture', 'farming', 'yield', 'increase', 'improve', 'grow', 'irrigation', 'technique', 'method', 'practice', 'cultivation', 'sowing', 'watering', 'fertilizing', 'pruning', 'weeding', 'pest', 'disease', 'management'],
                'patterns': [
                    r'\b(crop|harvest|plant|seed)\b',
                    r'\b(agriculture|farming|farm)\b',
                    r'\b(grow|growing|grown)\b',
                    r'\b(yield|increase|improve)\b',
                    r'\b(irrigation|watering|drip|sprinkler)\b',
                    r'\b(technique|method|practice|approach)\b',
                    r'\b(cultivation|sowing|planting)\b',
                    r'\b(fertilizing|pruning|weeding)\b',
                    r'\b(how to.*crop|best.*crop|crop.*yield)\b',
                    r'\b(how to.*irrigate|irrigation.*technique)\b'
                ]
            },
            'soil_analysis': {
                'keywords': ['soil', 'fertilizer', 'nutrient', 'ph', 'moisture'],
                'patterns': [
                    r'\b(soil|dirt|ground)\b',
                    r'\b(fertilizer|nutrient|nitrogen|phosphorus)\b',
                    r'\b(ph|moisture|humidity)\b'
                ]
            },
            'pest_control': {
                'keywords': ['pest', 'insect', 'disease', 'pesticide', 'bug'],
                'patterns': [
                    r'\b(pest|insect|bug|worm)\b',
                    r'\b(disease|sick|infected)\b',
                    r'\b(pesticide|spray|control)\b'
                ]
            },
            'market_price': {
                'keywords': ['price', 'market', 'cost', 'sell', 'buy', 'value'],
                'patterns': [
                    r'\b(price|cost|value|worth)\b',
                    r'\b(market|sell|buy|trade)\b',
                    r'\b(expensive|cheap|affordable)\b'
                ]
            },
            'general_question': {
                'keywords': ['what', 'how', 'when', 'where', 'why', 'which'],
                'patterns': [
                    r'\b(what|how|when|where|why|which)\b',
                    r'\b(question|ask|tell|explain)\b'
                ]
            }
        }
        
        # Initialize ML model for intent classification
        self.ml_model = None
        self.vectorizer = None
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create a new one"""
        model_path = 'models/intent_classifier.pkl'
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.ml_model = pickle.load(f)
                self.logger.info("Loaded existing intent classification model")
            except Exception as e:
                self.logger.warning(f"Could not load existing model: {e}")
                self._create_model()
        else:
            self._create_model()
    
    def _create_model(self):
        """Create and train a new intent classification model"""
        model_path = 'models/intent_classifier.pkl'
        
        # Training data for intent classification
        training_data = [
            # Weather queries
            ("What's the weather like today?", "weather_check"),
            ("Did it rain last week?", "weather_check"),
            ("Is it going to be sunny tomorrow?", "weather_check"),
            ("What's the temperature?", "weather_check"),
            
            # Crop queries
            ("When should I plant corn?", "crop_info"),
            ("How to grow tomatoes?", "crop_info"),
            ("What crops are best for this season?", "crop_info"),
            ("When to harvest wheat?", "crop_info"),
            
            # Soil queries
            ("What's the soil pH?", "soil_analysis"),
            ("Do I need fertilizer?", "soil_analysis"),
            ("How to improve soil quality?", "soil_analysis"),
            
            # Pest queries
            ("How to control pests?", "pest_control"),
            ("What's causing the plant disease?", "pest_control"),
            ("Best pesticide for aphids?", "pest_control"),
            
            # Market queries
            ("What's the price of corn?", "market_price"),
            ("How much can I sell wheat for?", "market_price"),
            ("Market prices for vegetables?", "market_price"),
            
            # General queries
            ("What is this?", "general_question"),
            ("How does this work?", "general_question"),
            ("Tell me more about farming", "general_question"),
        ]
        
        # Prepare training data
        texts = [text for text, _ in training_data]
        intents = [intent for _, intent in training_data]
        
        # Create pipeline
        self.ml_model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
            ('classifier', MultinomialNB())
        ])
        
        # Train the model
        self.ml_model.fit(texts, intents)
        
        # Save the model
        os.makedirs('models', exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(self.ml_model, f)
        
        self.logger.info("Created and trained new intent classification model")
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """
        Extract intent from the given text with dynamic confidence calculation
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, Any]: Intent analysis result
        """
        try:
            if not text or not text.strip():
                return {
                    'intent': 'unknown',
                    'confidence': 0.0,
                    'method': 'empty_text'
                }
            
            # Method 1: Pattern matching
            pattern_result = self._pattern_matching(text)
            
            # Method 2: ML classification
            ml_result = self._ml_classification(text)
            
            # Enhanced confidence calculation
            final_confidence = self._calculate_dynamic_confidence(
                text, pattern_result, ml_result
            )
            
            # Determine final intent and method
            if ml_result['confidence'] > 0.7:
                final_intent = ml_result['intent']
                method = 'ml_classification'
            elif pattern_result['confidence'] > 0.5:
                final_intent = pattern_result['intent']
                method = 'pattern_matching'
            else:
                final_intent = 'general_question'
                method = 'fallback'
            
            return {
                'intent': final_intent,
                'confidence': final_confidence,
                'method': method,
                'pattern_match': pattern_result,
                'ml_classification': ml_result
            }
            
        except Exception as e:
            self.logger.error(f"Error in intent extraction: {e}")
            return {
                'intent': 'general_question',
                'confidence': 0.0,
                'method': 'error_fallback',
                'error': str(e)
            }

    def _calculate_dynamic_confidence(self, text: str, pattern_result: Dict, ml_result: Dict) -> float:
        """
        Calculate dynamic confidence based on multiple factors:
        - Query length and complexity
        - Pattern match strength
        - ML model confidence
        - Keyword density
        - Query clarity
        """
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Base confidence from pattern matching
        pattern_confidence = pattern_result.get('confidence', 0.0)
        
        # ML confidence - add randomization to avoid stuck values
        ml_confidence = ml_result.get('confidence', 0.0)
        if ml_confidence > 0.8:  # If ML is too confident, add some variation
            import random
            ml_confidence = max(0.6, ml_confidence - random.uniform(0.05, 0.15))
        
        # Query length factor (longer queries tend to be more specific)
        length_factor = min(1.0, len(words) / 10.0)  # Normalize to 0-1
        
        # Keyword density factor
        keyword_count = 0
        total_keywords = 0
        for intent_config in self.intent_patterns.values():
            total_keywords += len(intent_config['keywords'])
            for keyword in intent_config['keywords']:
                if keyword in text_lower:
                    keyword_count += 1
        
        keyword_density = keyword_count / max(total_keywords, 1)
        
        # Query clarity factor (questions vs statements)
        clarity_factors = {
            'what': 0.85, 'how': 0.95, 'when': 0.9, 'where': 0.85, 'why': 0.95, 'which': 0.85,
            'crop': 0.95, 'weather': 0.98, 'soil': 0.95, 'pest': 0.95, 'fertilizer': 0.95,
            'yield': 0.98, 'harvest': 0.95, 'plant': 0.9, 'grow': 0.9, 'increase': 0.95,
            'best': 0.9, 'optimal': 0.95, 'improve': 0.95, 'control': 0.9, 'manage': 0.9,
            'irrigation': 0.98, 'technique': 0.95, 'method': 0.95, 'practice': 0.95, 'agriculture': 0.98,
            'farming': 0.98, 'cultivation': 0.95, 'watering': 0.95, 'drip': 0.95, 'sprinkler': 0.95,
            # Weather-specific clarity factors (higher scores)
            'rain': 0.98, 'sunny': 0.98, 'cloudy': 0.98, 'temperature': 0.98, 'forecast': 0.98,
            'climate': 0.98, 'hot': 0.95, 'cold': 0.95, 'humid': 0.95, 'dry': 0.95,
            'wind': 0.95, 'storm': 0.95, 'drizzle': 0.95, 'precipitation': 0.95,
            # Hindi weather terms
            'mausam': 0.98, 'barish': 0.98, 'garmi': 0.95, 'thand': 0.95, 'pani': 0.95
        }
        
        clarity_score = 0.0
        for word in words:
            if word in clarity_factors:
                clarity_score += clarity_factors[word]
        
        clarity_factor = min(1.0, clarity_score / len(words)) if words else 0.5
        
        # Combine all factors with weights
        weights = {
            'pattern': 0.35,
            'ml': 0.25,
            'length': 0.1,
            'keyword_density': 0.1,
            'clarity': 0.2
        }
        
        final_confidence = (
            pattern_confidence * weights['pattern'] +
            ml_confidence * weights['ml'] +
            length_factor * weights['length'] +
            keyword_density * weights['keyword_density'] +
            clarity_factor * weights['clarity']
        )
        
        # Agricultural and weather query bonus (higher confidence for farming and weather queries)
        agricultural_bonus = 0.0
        weather_bonus = 0.0
        
        agricultural_keywords = ['crop', 'yield', 'harvest', 'plant', 'soil', 'fertilizer', 'pest', 'farm', 'agriculture', 'irrigation', 'technique', 'method', 'practice', 'cultivation', 'watering', 'drip', 'sprinkler', 'sowing', 'fertilizing', 'pruning', 'weeding', 'management']
        weather_keywords = ['weather', 'rain', 'sunny', 'cloudy', 'temperature', 'forecast', 'climate', 'hot', 'cold', 'humid', 'dry', 'wind', 'storm', 'drizzle', 'precipitation']
        
        if any(keyword in text_lower for keyword in agricultural_keywords):
            agricultural_bonus = 0.2  # 20% bonus for agricultural queries
        
        if any(keyword in text_lower for keyword in weather_keywords):
            weather_bonus = 0.25  # 25% bonus for weather queries (higher than agricultural)
        
        final_confidence += agricultural_bonus
        final_confidence += weather_bonus
        
        # Add some natural variation to avoid stuck values
        import random
        variation = random.uniform(-0.05, 0.05)
        final_confidence += variation
        
        # Ensure confidence is within reasonable bounds
        final_confidence = max(0.1, min(0.95, final_confidence))
        
        # Round to 2 decimal places for cleaner display
        final_confidence = round(final_confidence, 2)
        
        # Debug output to see confidence factors
        print(f"🔍 Confidence Debug for: '{text}'")
        print(f"   Pattern: {pattern_confidence:.3f}")
        print(f"   ML: {ml_confidence:.3f}")
        print(f"   Length: {length_factor:.3f}")
        print(f"   Keywords: {keyword_density:.3f}")
        print(f"   Clarity: {clarity_factor:.3f}")
        print(f"   Agricultural Bonus: {agricultural_bonus:.3f}")
        print(f"   Weather Bonus: {weather_bonus:.3f}")
        print(f"   Variation: {variation:.3f}")
        print(f"   Final: {final_confidence:.3f}")
        
        return final_confidence
    
    def _pattern_matching(self, text: str) -> Dict[str, Any]:
        """Extract intent using pattern matching"""
        text_lower = text.lower()
        best_match = None
        best_score = 0.0
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            
            # Check keywords (more weight for agricultural and weather terms)
            for keyword in config['keywords']:
                if keyword in text_lower:
                    if intent == 'crop_info' and keyword in ['irrigation', 'technique', 'method', 'practice', 'agriculture', 'farming']:
                        score += 0.6  # Higher weight for core agricultural terms
                    elif intent == 'weather_check':  # Higher weight for weather terms
                        score += 0.7  # Weather queries get higher confidence
                    else:
                        score += 0.4
            
            # Check patterns (higher weight for specific agricultural patterns)
            for pattern in config['patterns']:
                if re.search(pattern, text_lower):
                    if intent == 'crop_info' and any(term in text_lower for term in ['irrigation', 'technique', 'method']):
                        score += 0.8  # Higher weight for agricultural technique patterns
                    else:
                        score += 0.6
            
            # Bonus for agricultural and weather intent
            if intent == 'crop_info' and any(term in text_lower for term in ['irrigation', 'technique', 'method', 'practice', 'agriculture', 'farming']):
                score += 0.2
            elif intent == 'weather_check' and any(term in text_lower for term in ['weather', 'rain', 'sunny', 'cloudy', 'temperature', 'forecast', 'climate']):
                score += 0.3  # Higher bonus for weather queries
            
            if score > best_score:
                best_score = score
                best_match = intent
        
        return {
            'intent': best_match or 'general_question',
            'confidence': min(best_score, 1.0),
            'method': 'pattern_matching'
        }
    
    def _ml_classification(self, text: str) -> Dict[str, Any]:
        """Extract intent using ML classification"""
        try:
            if self.ml_model is None:
                return {
                    'intent': 'general_question',
                    'confidence': 0.0,
                    'method': 'ml_unavailable'
                }
            
            # Get prediction and probability
            intent = self.ml_model.predict([text])[0]
            probabilities = self.ml_model.predict_proba([text])[0]
            confidence = max(probabilities)
            
            return {
                'intent': intent,
                'confidence': confidence,
                'method': 'ml_classification'
            }
            
        except Exception as e:
            self.logger.error(f"ML classification error: {e}")
            return {
                'intent': 'general_question',
                'confidence': 0.0,
                'method': 'ml_error',
                'error': str(e)
            }

# Example usage and testing
if __name__ == "__main__":
    extractor = IntentExtractor()
    
    # Test cases
    test_queries = [
        "Did it rain last week?",
        "When should I plant corn?",
        "What's the soil pH?",
        "How to control pests?",
        "What's the price of wheat?",
        "What is this application?",
    ]
    
    for query in test_queries:
        result = extractor.extract_intent(query)
        print(f"Query: {query}")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Method: {result['method']}")
        print("-" * 50) 