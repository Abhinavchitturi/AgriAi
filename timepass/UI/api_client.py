"""
API Client for AgriAI Assistant
Handles all communication with the backend FastAPI server
"""

import requests
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import API_CONFIG, ERROR_MESSAGES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgriAIClient:
    """Client for communicating with AgriAI backend API"""
    
    def __init__(self):
        self.base_url = API_CONFIG["BASE_URL"]
        self.timeout = API_CONFIG["TIMEOUT"]
        self.retry_attempts = API_CONFIG["RETRY_ATTEMPTS"]
        self.retry_delay = API_CONFIG["RETRY_DELAY"]
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code < 500:  # Don't retry client errors
                    return response
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout error on attempt {attempt + 1}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception("Max retry attempts reached")
    
    def send_query(self, query: str, language: str = "en", user_id: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a query to the backend API
        
        Args:
            query: The user's question
            language: Language code (en, hi, te, ta, etc.)
            user_id: Optional user identifier
            location: Optional location for weather queries
            
        Returns:
            Dict containing answer, source, confidence, etc.
        """
        try:
            payload = {
                "query": query.strip(),
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "context": {
                    "location": location
                } if location else {}
            }
            
            logger.info(f"Sending query: {query[:50]}... in language: {language}")
            
            # Use RAG endpoint for better agricultural responses
            endpoint = "/query-rag" if "crop" in query.lower() or "seed" in query.lower() or "variety" in query.lower() or "suitable" in query.lower() else "/query"
            
            response = self._make_request(
                method="POST",
                endpoint=endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Received response with confidence: {result.get('confidence', 'N/A')}")
                return result
                
            elif response.status_code == 400:
                error_data = response.json()
                return {
                    "answer": f"Invalid request: {error_data.get('detail', 'Bad request')}",
                    "source": "Input Error",
                    "confidence": 0.0,
                    "error": True
                }
                
            elif response.status_code == 429:
                return {
                    "answer": "Too many requests. Please wait a moment and try again.",
                    "source": "Rate Limit",
                    "confidence": 0.0,
                    "error": True
                }
                
            else:
                return {
                    "answer": f"Server error occurred (Status: {response.status_code}). Please try again later.",
                    "source": "Server Error",
                    "confidence": 0.0,
                    "error": True
                }
                
        except requests.exceptions.ConnectionError:
            logger.error("Connection error - backend server not reachable")
            return {
                "answer": ERROR_MESSAGES["en"]["connection_error"],
                "source": "Connection Error",
                "confidence": 0.0,
                "error": True
            }
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return {
                "answer": ERROR_MESSAGES["en"]["timeout_error"],
                "source": "Timeout Error", 
                "confidence": 0.0,
                "error": True
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in send_query: {e}")
            return {
                "answer": f"{ERROR_MESSAGES['en']['general_error']}: {str(e)}",
                "source": "System Error",
                "confidence": 0.0,
                "error": True
            }
    
    def get_chat_history(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get chat history from backend
        
        Args:
            user_id: Optional user identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of chat history entries
        """
        try:
            params = {"limit": limit}
            if user_id:
                params["user_id"] = user_id
                
            response = self._make_request(
                method="GET",
                endpoint="/history",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get history: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def save_conversation(self, query: str, answer: str, language: str, 
                         source: str = "", confidence: float = 0.0,
                         user_id: Optional[str] = None) -> bool:
        """
        Save a conversation to backend
        
        Args:
            query: User's question
            answer: AI's response
            language: Language code
            source: Source of the answer
            confidence: Confidence score
            user_id: Optional user identifier
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            payload = {
                "query": query,
                "answer": answer,
                "language": language,
                "source": source,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
            response = self._make_request(
                method="POST",
                endpoint="/conversation",
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
    def get_suggestions(self, language: str = "en", category: str = "general") -> List[str]:
        """
        Get question suggestions from backend
        
        Args:
            language: Language code
            category: Category of suggestions (crops, fertilizer, pest, etc.)
            
        Returns:
            List of suggested questions
        """
        try:
            params = {
                "language": language,
                "category": category
            }
            
            response = self._make_request(
                method="GET",
                endpoint="/suggestions",
                params=params
            )
            
            if response.status_code == 200:
                return response.json().get("suggestions", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def health_check(self) -> bool:
        """
        Check if backend server is healthy
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/health",
                timeout=5  # Quick timeout for health check
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages from backend
        
        Returns:
            List of language dictionaries with code and name
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/languages"
            )
            
            if response.status_code == 200:
                return response.json().get("languages", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting supported languages: {e}")
            return []

# Mock API Client for development/testing
class MockAgriAIClient:
    """Mock client for testing without backend"""
    
    def __init__(self):
        self.conversations = []
        
    def send_query(self, query: str, language: str = "en", user_id: Optional[str] = None) -> Dict[str, Any]:
        """Mock query response"""
        # Simulate processing time
        time.sleep(1)
        
        # Generate mock response based on keywords
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["wheat", "गेहूं", "గోధుమ", "கோதுமை"]):
            answer = "For wheat cultivation, ensure proper soil preparation, use certified seeds, apply balanced fertilizers (NPK 120:60:40 kg/ha), and maintain adequate irrigation. Harvest when moisture content is 20-25%."
            source = "Agricultural Guidelines DB + Expert Knowledge"
            confidence = 0.85
            
        elif any(keyword in query_lower for keyword in ["tomato", "टमाटर", "టమాటా", "தக்காளி"]):
            answer = "Tomatoes require well-drained soil with pH 6.0-7.0. Use organic fertilizers, provide support for climbing varieties, and ensure regular watering. Watch for common diseases like blight."
            source = "Horticultural Research Institute"
            confidence = 0.92
            
        elif any(keyword in query_lower for keyword in ["fertilizer", "उर्वरक", "ఎరువు", "உரம்"]):
            answer = "Choose fertilizers based on soil test results. For general crops, NPK ratios of 10:26:26 for flowering and 20:20:20 for growth phase work well. Apply organic compost for long-term soil health."
            source = "Soil Science Department"
            confidence = 0.78
            
        elif any(keyword in query_lower for keyword in ["pest", "कीट", "కీటకాలు", "பூச்சி"]):
            answer = "Integrated Pest Management (IPM) is recommended. Use neem-based pesticides, encourage beneficial insects, practice crop rotation, and maintain field hygiene. Monitor regularly for early detection."
            source = "Entomology Research Center"
            confidence = 0.81
            
        else:
            answer = "Thank you for your agriculture question. For specific guidance, please consult with local agricultural extension officers or visit your nearest Krishi Vigyan Kendra (KVK)."
            source = "General Agricultural Advisory"
            confidence = 0.65
        
        # Translate answer if not English (simplified)
        if language == "hi":
            answer = "कृषि संबंधी आपके प्रश्न के लिए धन्यवाद। विशिष्ट मार्गदर्शन के लिए, कृपया स्थानीय कृषि विस्तार अधिकारियों से परामर्श करें।"
        elif language == "te":
            answer = "మీ వ్యవసాయ ప్రశ్న కోసం ధన్యవాదాలు. నిర్దిష్ట మార్గదర్శకత్వం కోసం, దయచేసి స్థానిక వ్యవసాయ విస్తరణ అధికారులను సంప్రదించండి."
        elif language == "ta":
            answer = "உங்கள் விவசாய கேள்விக்கு நன்றி. குறிப்பிட்ட வழிகாட்டுதலுக்கு, உள்ளூர் விவசாய விரிவாக்க அதிகாரிகளை தொடர்பு கொள்ளவும்."
        
        return {
            "answer": answer,
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "language": language
        }
    
    def get_chat_history(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Mock chat history"""
        return self.conversations[-limit:] if self.conversations else []
    
    def save_conversation(self, query: str, answer: str, language: str, 
                         source: str = "", confidence: float = 0.0,
                         user_id: Optional[str] = None) -> bool:
        """Mock save conversation"""
        conversation = {
            "query": query,
            "answer": answer,
            "language": language,
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        self.conversations.append(conversation)
        return True
    
    def health_check(self) -> bool:
        """Mock health check"""
        return True
    
    def get_suggestions(self, language: str = "en", category: str = "general") -> List[str]:
        """Mock suggestions"""
        suggestions = {
            "en": [
                "How to increase crop yield?",
                "Best fertilizer for my soil?",
                "When to plant vegetables?",
                "How to control pests naturally?"
            ],
            "hi": [
                "फसल की पैदावार कैसे बढ़ाएं?",
                "मेरी मिट्टी के लिए सबसे अच्छा उर्वरक?",
                "सब्जियां कब लगाएं?",
                "प्राकृतिक रूप से कीटों को कैसे नियंत्रित करें?"
            ]
        }
        return suggestions.get(language, suggestions["en"])

# Create client instance
def get_api_client() -> AgriAIClient:
    """Get appropriate API client based on configuration"""
    from config import DEV_CONFIG
    
    if DEV_CONFIG.get("enable_mock_api", False):
        logger.info("Using Mock API Client")
        return MockAgriAIClient()
    else:
        logger.info("Using Real API Client")
        return AgriAIClient()