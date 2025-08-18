import streamlit as st
import requests
import time
import json
from datetime import datetime, timedelta
import base64
from io import BytesIO
import pandas as pd
from PIL import Image
import io
import hashlib
import re

# ================================
# PAGE CONFIGURATION
# ================================
st.set_page_config(
    page_title="AgriAI Pro Assistant",
    page_icon="🌾",
    layout="wide"
)

# ================================
# ADVANCED CSS STYLING
# ================================
def load_advanced_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Enhanced Header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        animation: slideInDown 1s ease-out;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        margin: 1rem 0;
        opacity: 0.9;
        animation: slideInUp 1s ease-out;
    }
    
    @keyframes slideInDown {
        from { transform: translateY(-30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes slideInUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    

    

    
    /* Enhanced Buttons */
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .primary-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
    }
    
    .primary-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .primary-button:hover::before {
        left: 100%;
    }
    
    /* Response Section */
    .response-section {
        
        border-radius: 20px;
        border-left: 6px solid #667eea;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        position: relative;
    }
    
    .answer-text {
        font-size: 1.15rem;
        line-height: 1.8;
        color: #2c3e50;
        margin-bottom: 1.5rem;
    }
    
    .source-info {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #28a745;
        font-size: 0.95rem;
        color: #155724;
        margin-top: 1rem;
    }
    
    .confidence-bar {
        width: 100%;
        height: 8px;
        background: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #ff6b6b 0%, #ffa500 50%, #4CAF50 100%);
        transition: width 1s ease;
    }
    
    /* Enhanced Loading */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 3rem;
    }
    
    .modern-spinner {
        width: 60px;
        height: 60px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    .loading-dots {
        display: flex;
        gap: 0.5rem;
    }
    
    .loading-dot {
        width: 12px;
        height: 12px;
        background: #667eea;
        border-radius: 50%;
        animation: bounce 1.4s ease-in-out infinite both;
    }
    
    .loading-dot:nth-child(1) { animation-delay: -0.32s; }
    .loading-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    /* Chat History */
    .history-item {
        background: white;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .history-item:hover {
        transform: translateX(5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .history-query {
        font-weight: 600;
        color: #667eea;
        margin-bottom: 0.8rem;
        font-size: 1.05rem;
    }
    
    .history-answer {
        color: #555;
        line-height: 1.6;
        margin-bottom: 0.8rem;
    }
    
    .history-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        color: #888;
        border-top: 1px solid #eee;
        padding-top: 0.8rem;
    }
    
    /* Image Upload Area */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e8ecf3 100%);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #f0f2ff 0%, #e0e5f0 100%);
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    /* Language Selector */
    .language-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .language-card {
        background: white;
        border: 2px solid #e8ecf3;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .language-card:hover {
        border-color: #667eea;
        background: #f8f9ff;
        transform: translateY(-2px);
    }
    
    .language-card.active {
        border-color: #667eea;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .hero-subtitle { font-size: 1.1rem; }
        .input-section, .response-section { padding: 1.5rem; }
        .stats-container { grid-template-columns: repeat(2, 1fr); }
        .language-grid { grid-template-columns: repeat(2, 1fr); }
    }
    
    @media (max-width: 480px) {
        .hero-title { font-size: 2rem; }
        .stats-container { grid-template-columns: 1fr; }
        .language-grid { grid-template-columns: 1fr; }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Notification Toast */
    .toast {
        position: fixed;
        top: 70px;
        right: 20px;image.png
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideInRight 0.5s ease;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }
    

    </style>
    """, unsafe_allow_html=True)

# ================================
# CONFIGURATION & CONSTANTS
# ================================

# Enhanced Language Configuration
LANGUAGES = {
    "🇺🇸 English": {"code": "en", "name": "English", "direction": "ltr"},
    "🇮🇳 हिंदी": {"code": "hi", "name": "Hindi", "direction": "ltr"},
    "🇮🇳 తెలుగు": {"code": "te", "name": "Telugu", "direction": "ltr"},
    "🇮🇳 தமிழ்": {"code": "ta", "name": "Tamil", "direction": "ltr"},
    "🇮🇳 ಕನ್ನಡ": {"code": "kn", "name": "Kannada", "direction": "ltr"},
    "🇮🇳 मराठी": {"code": "mr", "name": "Marathi", "direction": "ltr"},
    "🇮🇳 ਪੰਜਾਬੀ": {"code": "pa", "name": "Punjabi", "direction": "ltr"},
    "🇮🇳 ଓଡ଼ିଆ": {"code": "or", "name": "Odia (Oriya)", "direction": "ltr"}
}

LANGUAGE_HINTS = {
    "en": "Ask your agriculture question in English... e.g., 'How to increase crop yield?'",
    "hi": "अपना कृषि प्रश्न हिंदी में पूछें... जैसे, 'फसल की पैदावार कैसे बढ़ाएं?'",
    "te": "మీ వ్యవసాయ ప్రశ్నను తెలుగులో అడగండి... ఉదా., 'పంట దిగుబడిని ఎలా పెంచాలి?'",
    "ta": "உங்கள் விவசாய கேள்வியை தமிழில் கேளுங்கள்... உதா., 'பயிர் விளைச்சலை எவ்வாறு அதிகரிப்பது?'",
    "kn": "ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ... ಉದಾ., 'ಬೆಳೆ ಇಳುವರಿಯನ್ನು ಹೇಗೆ ಹೆಚ್ಚಿಸುವುದು?'",
    "mr": "आपला शेती प्रश्न मराठीत विचारा... उदा., 'पिकाचे उत्पादन कसे वाढवावे?'",
    "es": "Haga su pregunta agrícola en español... ej., '¿Cómo aumentar el rendimiento de cultivos?'",
    "fr": "Posez votre question agricole en français... ex., 'Comment augmenter le rendement des cultures?'"
}

# API Configuration
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FALLBACK_RESPONSES = {
    "connection_error": "🔌 I'm currently offline. Please check your internet connection and try again.",
    "timeout_error": "⏱️ Request timed out. Please try with a shorter question.",
    "server_error": "🛠️ Server is experiencing issues. Please try again later.",
    "unknown_error": "❌ An unexpected error occurred. Please try again."
}

# ================================
# SESSION STATE MANAGEMENT
# ================================
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'chat_history': [],
        'selected_language': "🇺🇸 English",
        'user_preferences': {
            'theme': 'light',
            'notifications': True,
            'voice_enabled': True,
            'auto_translate': False
        },
        'voice_input': "",
        'is_listening': False,
        'uploaded_images': [],
        'query_count': 0,
        'session_start': datetime.now(),
        'favorites': [],
        'recent_topics': [],
        'user_feedback': {},
        'location': None,
        'text_input': "",
        'location_input': "",
        'user_question': "",
        'user_location': "",
        'suggestion_clicked': None,
        'suggestion_counter': 0,
        'location_error': False,
        'query_error': False,
        'question_timestamp': 0,
        'clear_input_flag': False,
        'current_response': None,
        'show_response': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ================================
# API FUNCTIONS
# ================================
class APIClient:
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
    
    def send_query(self, query, language_code, image_data=None, location=None):
        """Enhanced query sending with image support"""
        try:
            payload = {
                "query": query,
                "language": language_code,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.get_user_id(),
                "session_id": self.get_session_id(),
                "context": {
                    "location": location,
                    "previous_queries": self.get_recent_context()
                }
            }
            
            if image_data:
                payload["image"] = image_data
            
            # Use RAG endpoint only
            response = self.session.post(
                f"{self.base_url}/query-rag",
                json=payload,
                timeout=60  # Increased timeout for RAG processing
            )
            
            if response.status_code == 200:
                result = response.json()
                self.update_analytics(query, result)
                return result
            else:
                return self.handle_error_response(response.status_code)
                
        except requests.exceptions.ConnectionError:
            return self.create_error_response("connection_error")
        except requests.exceptions.Timeout:
            return self.create_error_response("timeout_error")
        except Exception as e:
            return self.create_error_response("unknown_error", str(e))
    
    def get_chat_history(self, limit=20):
        """Get enhanced chat history"""
        try:
            response = self.session.get(
                f"{self.base_url}/history",
                params={"limit": limit, "user_id": self.get_user_id()}
            )
            if response.status_code == 200:
                return response.json()
            return st.session_state.chat_history
        except:
            return st.session_state.chat_history
    
    def get_analytics(self):
        """Get user analytics"""
        try:
            response = self.session.get(
                f"{self.base_url}/analytics",
                params={"user_id": self.get_user_id()}
            )
            if response.status_code == 200:
                return response.json()
            return self.get_default_analytics()
        except:
            return self.get_default_analytics()
    
    def get_user_id(self):
        """Generate or retrieve user ID"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = hashlib.md5(
                str(st.session_state.session_start).encode()
            ).hexdigest()[:12]
        return st.session_state.user_id
    
    def get_session_id(self):
        """Generate session ID"""
        return hashlib.md5(str(st.session_state.session_start).encode()).hexdigest()[:8]
    
    def get_recent_context(self):
        """Get recent queries for context"""
        return [chat['query'] for chat in st.session_state.chat_history[-3:]]
    
    def create_error_response(self, error_type, details=""):
        """Create standardized error response"""
        return {
            "answer": FALLBACK_RESPONSES.get(error_type, FALLBACK_RESPONSES["unknown_error"]),
            "source": "System Error",
            "confidence": 0.0,
            "error": True,
            "error_type": error_type,
            "details": details
        }
    
    def handle_error_response(self, status_code):
        """Handle HTTP error responses"""
        error_map = {
            400: "Invalid request format",
            401: "Authentication required",
            403: "Access forbidden",
            404: "Service not found",
            429: "Too many requests - please wait",
            500: "Server internal error",
            502: "Service temporarily unavailable",
            503: "Service maintenance mode"
        }
        
        error_msg = error_map.get(status_code, f"HTTP Error {status_code}")
        return self.create_error_response("server_error", error_msg)
    
    def update_analytics(self, query, response):
        """Update user analytics"""
        st.session_state.query_count += 1
        
        # Update recent topics
        topic = self.extract_topic(query)
        if topic and topic not in st.session_state.recent_topics:
            st.session_state.recent_topics.insert(0, topic)
            st.session_state.recent_topics = st.session_state.recent_topics[:10]
    
    def extract_topic(self, query):
        """Extract main topic from query"""
        # Simple keyword extraction - can be enhanced with NLP
        crops = ['wheat', 'rice', 'corn', 'tomato', 'potato', 'cotton', 'sugarcane']
        topics = ['fertilizer', 'pesticide', 'irrigation', 'soil', 'disease', 'pest']
        
        query_lower = query.lower()
        for crop in crops:
            if crop in query_lower:
                return crop
        for topic in topics:
            if topic in query_lower:
                return topic
        return None
    
    def get_default_analytics(self):
        """Get default analytics when API is unavailable"""
        return {
            "total_queries": st.session_state.query_count,
            "session_duration": str(datetime.now() - st.session_state.session_start).split('.')[0],
            "favorite_topics": st.session_state.recent_topics[:5],
            "accuracy_score": 0.85,
            "user_satisfaction": 4.2
        }

# Initialize API client
api_client = APIClient()

# ================================
# IMAGE PROCESSING
# ================================
def process_uploaded_image(uploaded_file):
    """Process uploaded image for analysis"""
    try:
        image = Image.open(uploaded_file)
        
        # Resize if too large
        max_size = (1024, 1024)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "data": img_str,
            "format": "JPEG",
            "size": image.size,
            "filename": uploaded_file.name
        }
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

# ================================
# UI COMPONENTS
# ================================
def render_hero_header():
    """Render enhanced hero header"""
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">🌾 AgriAI Pro</h1>
        <p class="hero-subtitle">
            Advanced AI-Powered Agricultural Assistant<br>
            🚀 Smart Farming • 🌱 Crop Optimization • 📊 Data-Driven Insights
        </p>
        <div style="background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 10px; margin-top: 1rem;">
            <h4 style="margin: 0; color: #fff;">🆕 New: RAG-Enhanced Intelligence</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.9;">
                Now powered by comprehensive agricultural data and 120-day weather forecasts!<br>
                Ask questions like "What's the weather tomorrow?" or "Best crops for current conditions?"
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)



def render_language_selector():
    """Enhanced language selector with visual cards"""
    st.subheader("🌐 Choose Your Language")
    
    # Create language grid
    cols = st.columns(4)
    languages = list(LANGUAGES.keys())
    
    for i, lang in enumerate(languages):
        with cols[i % 4]:
            is_selected = lang == st.session_state.selected_language
            
            # Use different button styling based on selection
            if is_selected:
                # Selected language - use primary button style
                if st.button(
                    f"✅ {lang}",
                    key=f"lang_{i}",
                    help=f"Currently selected: {LANGUAGES[lang]['name']}",
                    use_container_width=True,
                    type="primary"
                ):
                    # Button clicked but already selected - no action needed
                    pass
            else:
                # Unselected language - use secondary button style
                if st.button(
                    lang,
                    key=f"lang_{i}",
                    help=f"Click to select {LANGUAGES[lang]['name']}",
                    use_container_width=True
                ):
                    st.session_state.selected_language = lang
                    st.rerun()

def render_advanced_input_section():
    """Enhanced input section with text input only"""
    # Get current language settings
    current_lang = LANGUAGES[st.session_state.selected_language]
    hint_text = LANGUAGE_HINTS.get(current_lang["code"], LANGUAGE_HINTS["en"])
    
    # Handle suggestion clicks - set the question value before widget creation
    if 'suggestion_clicked' in st.session_state and st.session_state.suggestion_clicked:
        suggestion_text = st.session_state.suggestion_clicked
        st.session_state.user_question = suggestion_text

        # Clear the suggestion click flag
        del st.session_state.suggestion_clicked
    
    # Text input with enhanced features
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get the current question value - prioritize user input over suggestions
        current_question = st.session_state.get("user_question", "")
        
        # Check if we need to clear the input
        if st.session_state.get("clear_input_flag", False):
            current_question = ""
            st.session_state.user_question = ""
            st.session_state.clear_input_flag = False
        
        # Use a dynamic key that changes when the question content changes
        # This ensures the text area re-renders with the correct value
        question_key = f"user_question_input_{hash(current_question) if current_question else 'empty'}"
        
        # Add timestamp to force updates when needed
        if 'question_timestamp' not in st.session_state:
            st.session_state.question_timestamp = 0
        question_key = f"{question_key}_{st.session_state.question_timestamp}"
        

        
        # Create the text area with proper value binding
        # Use text_area for better user experience with longer questions
        # Force the value to be empty if session state is empty
        display_value = current_question if current_question else ""
        query = st.text_area(
            "Enter your agriculture question:",
            value=display_value,
            placeholder=hint_text,
            height=120,
            key=question_key,
            help="Ask detailed questions for better answers"
        )
        
        # If query is None but we have a session state value, use the session state
        if query is None and current_question:
            query = current_question
        
        # If query is empty but we have a session state value, prioritize session state
        if not query and current_question:
            query = current_question
        

        
        # Update session state with current input - preserve user typing
        if query is not None:  # Always update, even if empty (to handle user clearing)
            # Only update if the query is actually different to avoid unnecessary reruns
            if query != st.session_state.get("user_question", ""):
                # Don't clear the session state if query is empty but we have a session value
                if query == "" and st.session_state.get("user_question", ""):
                    pass  # Keep existing session state
                else:
                    st.session_state.user_question = query
                    # Clear any previous query errors
                    if 'query_error' in st.session_state:
                        del st.session_state.query_error
        
        # Quick suggestion buttons
        st.markdown("**💡 Quick Suggestions:**")
        suggestions = [
            "What will be the weather tomorrow?",
            "How to increase crop yield?",
            "Is it good weather for farming this week?",
            "Best fertilizer for vegetables?",
            "Will it rain in the next few days?",
            "What are suitable crops for current weather?",
        ]
        
        suggestion_cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with suggestion_cols[i % 2]:
                # Check if this suggestion is currently selected
                is_selected = st.session_state.get("user_question", "") == suggestion
                
                # Create button with visual feedback
                if st.button(
                    suggestion,
                    key=f"suggest_{i}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    # Set the suggestion and trigger rerun
                    st.session_state.user_question = suggestion  # Set immediately
                    st.session_state.suggestion_clicked = suggestion
                    # Force timestamp update to change the text input key
                    if 'question_timestamp' not in st.session_state:
                        st.session_state.question_timestamp = 0
                    st.session_state.question_timestamp += 1
                    st.rerun()
    
    with col2:
        # Location input (mandatory) - use session state to persist value
        current_location = st.session_state.get("user_location", "")
        location = st.text_input(
            "📍 Location *",
            value=current_location,
            placeholder="e.g., Punjab, India",
            key="location_input_field",
            help="Location is required for location-specific advice"
        )
        
        # Update session state with current location input (only if not empty)
        if location and location.strip():
            st.session_state.user_location = location.strip()
        elif location == "":  # Handle empty input
            st.session_state.user_location = ""
        
        # Show warning if location is empty
        if not location or location.strip() == "":
            st.warning("⚠️ Please enter your location to continue")
        else:
            # Location is valid, clear any previous location errors
            if 'location_error' in st.session_state:
                del st.session_state.location_error
        

    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_clicked = st.button(
            "🔍 Get AI Analysis",
            type="primary",
            use_container_width=True,
            help="Click to get your personalized agriculture advice"
        )
    
    # Get the current query value from the text area or session state
    # Handle the case where query might be None
    if query is None:
        final_query = st.session_state.get("user_question", "")
    else:
        final_query = query.strip() if query and query.strip() else st.session_state.get("user_question", "")
    
    # Update session state with the final query if we have one
    if final_query:
        st.session_state.user_question = final_query
    
    # Get the current location value from session state to ensure consistency
    final_location = st.session_state.get("user_location", "")
    
    return final_query, submit_clicked, final_location

def render_enhanced_response_section(response_data):
    """Enhanced response section with rich formatting"""
    if not response_data:
        return
    
    st.markdown('<div class="response-section">', unsafe_allow_html=True)
    
    # Response header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 🤖 AI Assistant Response")
        
        # Show generation time in the header if available
        if 'generation_time' in response_data:
            generation_time = response_data['generation_time']
            if generation_time < 1:
                time_display = f"{generation_time * 1000:.0f}ms"
            elif generation_time < 60:
                time_display = f"{generation_time:.1f}s"
            else:
                minutes = int(generation_time // 60)
                seconds = generation_time % 60
                time_display = f"{minutes}m {seconds:.1f}s"
            
            st.caption(f"⚡ Generated in {time_display}")
    
    with col2:
        if not response_data.get("error", False):
            confidence = response_data.get("confidence", 0.0)
            st.markdown(f"""
            <div style="text-align: right;">
                <small>Confidence: {confidence:.1%}</small>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {confidence * 100}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Main answer - handle both regular answer and ultra-fast mode
    processing_mode = response_data.get('processing_mode', 'Standard')
    is_ultra_fast = processing_mode == 'ultra_fast_direct'
    
    if is_ultra_fast and response_data.get('rag_response'):
        # Ultra-fast mode response
        answer = response_data['rag_response']
        st.markdown("### ⚡ Ultra-Fast Response")
    elif response_data.get('rag_response'):
        # RAG response available
        answer = response_data['rag_response']
    elif response_data.get("answer"):
        # Regular response
        answer = response_data["answer"]
    else:
        # Fallback
        answer = "No response available"
    
    # Enhanced formatting for better readability
    formatted_answer = format_response_text(answer)
    st.markdown(f'<div class="answer-text">{formatted_answer}</div>', unsafe_allow_html=True)
    
    # Enhanced RAG information display
    if not response_data.get("error", False):
        st.markdown("---")
        st.markdown("### 🔍 Processing Details")
        
        # Check if this is a RAG response or ultra-fast mode
        processing_mode = response_data.get('processing_mode', 'Standard')
        is_rag_response = 'RAG' in processing_mode
        is_ultra_fast = processing_mode == 'ultra_fast_direct'
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Show essential information only
            if 'location' in response_data:
                st.markdown(f"**Location:** {response_data.get('location', 'N/A')}")
            st.markdown(f"**Processing Mode:** {processing_mode}")
            
            # Show generation time if available
            if 'generation_time' in response_data:
                generation_time = response_data['generation_time']
                if generation_time < 1:
                    time_display = f"{generation_time * 1000:.0f}ms"
                elif generation_time < 60:
                    time_display = f"{generation_time:.1f}s"
                else:
                    minutes = int(generation_time // 60)
                    seconds = generation_time % 60
                    time_display = f"{minutes}m {seconds:.1f}s"
                
                st.markdown(f"**Generation Time:** {time_display}")
        
        with col2:
            if 'confidence' in response_data:
                confidence = response_data.get('confidence', 0.0)
                st.markdown(f"**Confidence Score:** {confidence:.1%}")
                
                # Enhanced confidence visualization
                if confidence >= 0.8:
                    confidence_color = "#4CAF50"  # Green
                    confidence_label = "High Confidence"
                elif confidence >= 0.5:
                    confidence_color = "#FFC107"  # Yellow
                    confidence_label = "Medium Confidence"
                else:
                    confidence_color = "#F44336"  # Red
                    confidence_label = "Low Confidence"
                
                # Custom confidence bar with color
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <div style="background: #e0e0e0; border-radius: 10px; padding: 2px;">
                        <div style="background: {confidence_color}; width: {confidence*100:.1f}%; 
                             height: 20px; border-radius: 8px; text-align: center; 
                             line-height: 20px; color: white; font-weight: bold;">
                            {confidence:.1%}
                        </div>
                    </div>
                    <small style="color: {confidence_color}; font-weight: bold;">{confidence_label}</small>
                </div>
                """, unsafe_allow_html=True)
            
            if 'source' in response_data:
                st.markdown(f"**Source:** {response_data.get('source', 'N/A')}")
        
        # Show RAG-specific information if available
        if is_rag_response and 'rag_info' in response_data:
            st.markdown("### 🧠 RAG Analysis Details")
            rag_info = response_data['rag_info']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Relevant Sources", 
                    rag_info.get('relevant_chunks', 0),
                    help="Number of relevant data sources used for this answer"
                )
            
            with col2:
                st.metric(
                    "Total Data Searched", 
                    rag_info.get('total_chunks_searched', 0),
                    help="Total data chunks searched in the knowledge base"
                )
            
            with col3:
                model_used = rag_info.get('model_used', 'RAG System')
                st.markdown(f"**AI Model:** {model_used}")
            
            with col4:
                if 'generation_time' in response_data:
                    generation_time = response_data['generation_time']
                    if generation_time < 1:
                        time_display = f"{generation_time * 1000:.0f}ms"
                    elif generation_time < 60:
                        time_display = f"{generation_time:.1f}s"
                    else:
                        minutes = int(generation_time // 60)
                        seconds = generation_time % 60
                        time_display = f"{minutes}m {seconds:.1f}s"
                    
                    st.metric(
                        "Generation Time",
                        time_display,
                        help="Time taken to generate this AI response"
                    )
            
            # Show context sources if available
            if rag_info.get('context_sources'):
                with st.expander("📚 Data Sources Used", expanded=False):
                    sources = rag_info['context_sources']
                    for i, source in enumerate(sources[:10], 1):  # Limit to first 10
                        if 'weather' in source.lower():
                            st.markdown(f"🌤️ {i}. {source}")
                        elif any(crop in source.lower() for crop in ['crop', 'agriculture', 'farm']):
                            st.markdown(f"🌾 {i}. {source}")
                        else:
                            st.markdown(f"📄 {i}. {source}")
                    
                    if len(sources) > 10:
                        st.markdown(f"... and {len(sources) - 10} more sources")
        
        # Show other processing details
        if 'timestamp' in response_data:
            st.markdown(f"**Timestamp:** {response_data.get('timestamp', 'N/A')}")
        
        # Display generation time
        if 'generation_time' in response_data:
            generation_time = response_data['generation_time']
            if generation_time < 1:
                time_display = f"{generation_time * 1000:.0f}ms"
            elif generation_time < 60:
                time_display = f"{generation_time:.1f}s"
            else:
                minutes = int(generation_time // 60)
                seconds = generation_time % 60
                time_display = f"{minutes}m {seconds:.1f}s"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #00b894 0%, #00a085 100%); color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                <h4>⚡ Response Generation Time</h4>
                <h2>{time_display}</h2>
                <p>AI response generated in {time_display}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Weather information (if available)
    weather_data = response_data.get("weather_data")
    

    
    if weather_data and not response_data.get("error", False) and 'error' not in weather_data:
        st.markdown("### 🌤️ Current Weather")
        
        # Weather information display
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                <h3>🌡️ Temperature</h3>
                <h2>{weather_data.get('temperature', 'N/A')}°C</h2>
                <p>Feels like {weather_data.get('feels_like', 'N/A')}°C</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                <h3>💧 Humidity</h3>
                <h2>{weather_data.get('humidity', 'N/A')}</h2>
                <p>Wind: {weather_data.get('wind_speed', 'N/A')} m/s</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #00b894 0%, #00a085 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                <h3>🌱 Moisture</h3>
                <h2>{weather_data.get('moisture', 'N/A')}</h2>
                <p>Soil moisture level</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                <h3>🌤️ Conditions</h3>
                <h2>{weather_data.get('description', 'N/A').title()}</h2>
                <p>Location: {response_data.get('location', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Add timeline information if available
        timeline_info = response_data.get("timeline_info", {})
        if timeline_info:
            st.markdown("---")
            st.markdown("### 📅 Timeline Information")
            
            timeline_col1, timeline_col2 = st.columns(2)
            
            with timeline_col1:
                st.info(f"""
                **📊 Data Period:** {timeline_info.get('description', 'N/A')}
                """)
            
            with timeline_col2:
                st.info(f"""
                **📈 Data Points:** {timeline_info.get('data_points', 'N/A')} days
                """)
    
    # Optional debug section for development (hidden by default)
    if st.session_state.get("show_debug", False):
        with st.expander("🔧 Debug Information", expanded=False):
            st.markdown("### Raw Response Data")
            st.json(response_data)
    
    # Clean response analysis (no duplication)
    
    # Additional response features
    col1, col2 = st.columns(2)
    
    with col1:
        # Source information
        if "source" in response_data and not response_data.get("error", False):
            st.markdown(f"""
            <div class="source-info">
                <strong>📚 Source:</strong> {response_data["source"]}<br>
                <strong>🔍 Category:</strong> {response_data.get("category", "General Agriculture")}<br>
                <strong>⚡ Response Time:</strong> {response_data.get("response_time", "< 7s")}<br>
                <strong>🚀 Generation Time:</strong> {response_data.get("generation_time", 0.0):.2f}s
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Action buttons
        st.markdown("**Quick Actions:**")
        
        action_cols = st.columns(2)
        
        with action_cols[0]:
            if st.button("❤️ Like", key="like_response", help="Mark as helpful"):
                add_feedback("like", response_data)
                st.success("Thanks for your feedback!")
        
        with action_cols[1]:
            if st.button("📎 Save", key="save_response", help="Save to favorites"):
                add_to_favorites(response_data)
                st.success("Saved to favorites!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def format_response_text(text):
    """Format response text with better styling"""
    import re

    # Convert bullet points
    text = re.sub(r'^\* (.+)', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.+)', r'• \1', text, flags=re.MULTILINE)

    # Convert numbered lists
    text = re.sub(r'^(\d+)\. (.+)', r'<strong>\1.</strong> \2', text, flags=re.MULTILINE)

    # Bold important terms
    important_terms = [
        'temperature', 'humidity', 'pH', 'nitrogen', 'phosphorus', 'potassium',
        'fertilizer', 'pesticide', 'irrigation', 'harvest', 'planting', 'soil'
    ]

    for term in important_terms:
        text = re.sub(f'\\b{term}\\b', f'<strong>{term}</strong>', text, flags=re.IGNORECASE)

    # Convert line breaks to paragraphs
    paragraphs = text.split('\n\n')
    formatted_paragraphs = [f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()]

    return ''.join(formatted_paragraphs)



def render_modern_loading():
    """Enhanced loading animation"""
    st.markdown("""
    <div class="loading-container">
        <div class="modern-spinner"></div>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        <p style="color: #667eea; font-weight: 500; margin-top: 1rem;">
            🧠 AI is analyzing your question...
        </p>
    </div>
    """, unsafe_allow_html=True)

# Chat history is now handled in the sidebar

def filter_chat_history(history, search_query, filter_language, sort_order):
    """Filter chat history based on criteria"""
    filtered = history
    
    # Filter by search query
    if search_query:
        filtered = [
            chat for chat in filtered
            if search_query.lower() in chat['query'].lower() or
               search_query.lower() in chat['answer'].lower()
        ]
    
    # Filter by language
    if filter_language != "All":
        filtered = [
            chat for chat in filtered
            if chat.get('language', '') == filter_language
        ]
    
    # Sort results
    if sort_order == "Recent First":
        filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)
    elif sort_order == "Oldest First":
        filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''))
    
    return filtered

# Chat history functions are now simplified and moved to the sidebar



# ================================
# UTILITY FUNCTIONS
# ================================
def add_to_history(query, response, language=None, location=None):
    """Add conversation to enhanced history"""
    chat_entry = {
        "query": query,
        "answer": response.get("rag_response") or response.get("answer", "No response"),
        "source": response.get("source", "AI Assistant"),
        "confidence": response.get("confidence", 0.0),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": language or st.session_state.selected_language,
        "location": location,
        "category": response.get("category", "General"),
        "response_time": response.get("response_time", "< 1s"),
        "generation_time": response.get("generation_time", 0.0),
        "error": response.get("error", False)
    }
    
    st.session_state.chat_history.append(chat_entry)
    
    # Keep only last 50 conversations for performance
    if len(st.session_state.chat_history) > 50:
        st.session_state.chat_history = st.session_state.chat_history[-50:]

def add_feedback(feedback_type, response_data):
    """Add user feedback for response"""
    answer_text = response_data.get("rag_response") or response_data.get("answer", "No response")
    feedback_id = hashlib.md5(
        (answer_text + str(datetime.now())).encode()
    ).hexdigest()[:8]
    
    st.session_state.user_feedback[feedback_id] = {
        "type": feedback_type,
        "timestamp": datetime.now().isoformat(),
        "response": answer_text[:100]  # Store snippet
    }

def add_to_favorites(response_data):
    """Add response to user favorites"""
    favorite_item = {
        "answer": response_data.get("rag_response") or response_data.get("answer", "No response"),
        "source": response_data.get("source", "AI Assistant"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": response_data.get("category", "General")
    }
    
    st.session_state.favorites.append(favorite_item)
    
    # Keep only last 20 favorites
    if len(st.session_state.favorites) > 20:
        st.session_state.favorites = st.session_state.favorites[-20:]

def show_notification(message, type="success"):
    """Show notification toast"""
    color_map = {
        "success": "#4CAF50",
        "error": "#f44336",
        "warning": "#ff9800",
        "info": "#2196F3"
    }
    
    st.markdown(f"""
    <div class="toast" style="background: {color_map.get(type, '#4CAF50')};">
        {message}
    </div>
    <script>
    setTimeout(function() {{
        document.querySelector('.toast').style.opacity = '0';
        setTimeout(function() {{
            document.querySelector('.toast').remove();
        }}, 500);
    }}, 3000);
    </script>
    """, unsafe_allow_html=True)

def export_chat_history():
    """Export chat history as downloadable file"""
    if not st.session_state.chat_history:
        return None
    
    # Convert to DataFrame for easy export
    df = pd.DataFrame(st.session_state.chat_history)
    
    # Create Excel buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Chat History', index=False)
        
        # Add analytics sheet
        analytics_data = {
            'Metric': ['Total Questions', 'Session Duration', 'Average Confidence', 'Most Common Language', 'Average Generation Time'],
            'Value': [
                len(st.session_state.chat_history),
                str(datetime.now() - st.session_state.session_start).split('.')[0],
                f"{df['confidence'].mean():.2%}" if 'confidence' in df.columns else "N/A",
                st.session_state.selected_language,
                f"{df['generation_time'].mean():.2f}s" if 'generation_time' in df.columns and df['generation_time'].notna().any() else "N/A"
            ]
        }
        pd.DataFrame(analytics_data).to_excel(writer, sheet_name='Analytics', index=False)
    
    return buffer.getvalue()

# ================================
# CHAT HISTORY SIDEBAR
# ================================
def render_chat_history_sidebar():
    """Render chat history sidebar"""
    with st.sidebar:
        st.markdown("## 💬 Chat History")
        
        if not st.session_state.chat_history:
            st.info("No chat history yet. Start asking questions!")
            return
        
        # Search functionality
        search_query = st.text_input("🔍 Search chats", placeholder="Search your questions...")
        
        # Filter by language
        filter_language = st.selectbox(
            "🌐 Language",
            ["All"] + list(LANGUAGES.keys()),
            index=0
        )
        
        # Filter and display history
        filtered_history = filter_chat_history(
            st.session_state.chat_history,
            search_query,
            filter_language,
            "Recent First"
        )
        
        # Display chat history
        for i, chat in enumerate(filtered_history[-15:]):  # Show last 15
            with st.expander(f"Q{i+1}: {chat['query'][:50]}{'...' if len(chat['query']) > 50 else ''}", expanded=False):
                st.markdown(f"**Question:** {chat['query']}")
                st.markdown(f"**Answer:** {chat['answer'][:150]}{'...' if len(chat['answer']) > 150 else ''}")
                
                # Display generation time if available
                generation_time = chat.get('generation_time', 0.0)
                if generation_time > 0:
                    if generation_time < 1:
                        time_display = f"{generation_time * 1000:.0f}ms"
                    elif generation_time < 60:
                        time_display = f"{generation_time:.1f}s"
                    else:
                        minutes = int(generation_time // 60)
                        seconds = generation_time % 60
                        time_display = f"{minutes}m {seconds:.1f}s"
                    st.caption(f"🕒 {chat.get('timestamp', 'Unknown time')} | 🌐 {chat.get('language', 'Unknown')} | 📍 {chat.get('location', 'Unknown')} | ⚡ {time_display}")
                else:
                    st.caption(f"🕒 {chat.get('timestamp', 'Unknown time')} | 🌐 {chat.get('language', 'Unknown')} | 📍 {chat.get('location', 'Unknown')}")
                
                # Show full answer in expandable
                with st.expander("View full answer", expanded=False):
                    st.markdown(chat['answer'])
        
        # Export button
        st.divider()
        if st.button("📊 Export Chat History", use_container_width=True):
            if st.session_state.chat_history:
                export_data = export_chat_history()
                if export_data:
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=export_data,
                        file_name=f"agriai_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.warning("No chat history to export")
        
        # Quick stats
        st.divider()
        st.markdown("### 📊 Quick Stats")
        st.metric("Questions Asked", st.session_state.query_count)
        st.metric("Session Time", str(datetime.now() - st.session_state.session_start).split('.')[0])

# ================================
# MAIN APPLICATION LOGIC
# ================================
def main():
    """Main application function with enhanced features"""
    # Load CSS and initialize
    load_advanced_css()
    initialize_session_state()
    
    # Render chat history sidebar
    render_chat_history_sidebar()
    
    # Main content area
    with st.container():
        # Hero header
        render_hero_header()
        
        # Language selector
        render_language_selector()
        
        # Main input section
        query, submit_clicked, location = render_advanced_input_section()
        
        # Display stored response if available
        if st.session_state.get("show_response", False) and st.session_state.get("current_response"):
            st.markdown("### 🤖 AI Assistant Response")
            render_enhanced_response_section(st.session_state.current_response)
            
            # Show success message after response
            if not st.session_state.current_response.get("error", False):
                st.success("✅ Response generated successfully! You can now ask another question.")
        
        # Process query
        if submit_clicked:
            # Get values directly from the function return
            actual_query = query.strip() if query else ""
            actual_location = location.strip() if location else ""
            
            # Clear previous response when new query is submitted
            st.session_state.show_response = False
            st.session_state.current_response = None
            
            # Clear any previous error messages
            if 'location_error' in st.session_state:
                del st.session_state.location_error
            if 'query_error' in st.session_state:
                del st.session_state.query_error
            
            # More detailed validation with better error messages
            if not actual_location:
                st.error(f"❌ Location is required. Current location: '{actual_location}'")
                show_notification("Location is required", "error")
                st.session_state.location_error = True
            elif not actual_query:
                st.error(f"❌ Please enter a question before submitting. Current query: '{actual_query}'")
                show_notification("Please provide input before submitting", "warning")
                st.session_state.query_error = True
            else:
                current_lang = LANGUAGES[st.session_state.selected_language]
                
                # Show quick loading indicator and capture timing
                start_time = time.time()
                
                # Create a placeholder for the loading message
                loading_placeholder = st.empty()
                
                with st.spinner("🤖 Generating AI response..."):
                    # Send to backend with enhanced parameters
                    response_data = api_client.send_query(
                        actual_query.strip(),
                        current_lang["code"],
                        image_data=None,
                        location=actual_location.strip()
                    )
                
                # Clear the loading placeholder
                loading_placeholder.empty()
                
                # Calculate response time
                end_time = time.time()
                response_time = end_time - start_time
                
                # Add response time to the response data
                response_data["generation_time"] = response_time
                
                # Store response in session state for persistent display
                st.session_state.current_response = response_data
                st.session_state.show_response = True
                
                # Add to history with enhanced data
                add_to_history(
                    actual_query.strip(),
                    response_data,
                    language=st.session_state.selected_language,
                    location=actual_location.strip()
                )
                
                # Increment query count for stats
                st.session_state.query_count += 1
                
                # Show success notification
                if not response_data.get("error", False):
                    # Format generation time for notification
                    generation_time = response_data.get("generation_time", 0.0)
                    if generation_time < 1:
                        time_display = f"{generation_time * 1000:.0f}ms"
                    elif generation_time < 60:
                        time_display = f"{generation_time:.1f}s"
                    else:
                        minutes = int(generation_time // 60)
                        seconds = generation_time % 60
                        time_display = f"{minutes}m {seconds:.1f}s"
                    
                    show_notification(f"✅ Response generated successfully in {time_display}!")
                    
                    # Clear the question input for the next query immediately
                    st.session_state.user_question = ""
                    # Force a significant timestamp change to ensure new key
                    st.session_state.question_timestamp = st.session_state.get('question_timestamp', 0) + 100
                    # Set a flag to indicate we need to clear the input
                    st.session_state.clear_input_flag = True
                    
                    # Rerun to refresh UI with cleared input and show response
                    st.rerun()
                else:
                    show_notification("⚠️ There was an issue with your request", "warning")
        
        # Chat history is now displayed in the sidebar
        
        # Spacer to push footer down
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Advanced footer with additional information - always visible
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h4>🌾 Agriculture Focus</h4>
                <p>Specialized in crop management, soil health, pest control, and sustainable farming practices.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h4>🤖 AI Technology</h4>
                <p>Powered by advanced machine learning models trained on comprehensive agricultural datasets.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h4>🌍 Global Support</h4>
                <p>Supporting farmers worldwide with localized advice and multilingual assistance.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Final footer
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem; padding: 2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px;">
            <p><strong>💡 Pro Tips for Better Results:</strong></p>
            <p>🎯 Ask specific questions • 📸 Upload clear images • 🌐 Use your native language • 📍 Include location for regional advice</p>
            <br>
            <p><strong>🔒 Privacy:</strong> Your data is secure and not shared with third parties</p>
            <p><strong>📞 Support:</strong> Need help? Contact our agricultural experts</p>
            <br>
            <p>© 2024 AgriAI Pro - Empowering farmers with intelligent technology</p>
        </div>
        """, unsafe_allow_html=True)

# ================================
# APPLICATION ENTRY POINT
# ================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #666;">
            <h3>🔧 Something went wrong</h3>
            <p>Please refresh the page or try again later.</p>
            <p>If the problem persists, please contact support.</p>
        </div>
        """, unsafe_allow_html=True)