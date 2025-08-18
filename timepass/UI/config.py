"""
Configuration file for AgriAI Assistant UI
Contains all the settings, constants, and configuration data
"""

import os
from typing import Dict, List

# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_CONFIG = {
    "BASE_URL": os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),  # Your FastAPI backend URL
    "TIMEOUT": int(os.getenv("UI_TIMEOUT", "30")),  # seconds
    "RETRY_ATTEMPTS": int(os.getenv("UI_RETRY_ATTEMPTS", "3")),
    "RETRY_DELAY": int(os.getenv("UI_RETRY_DELAY", "1"))  # seconds
}

# Language Configuration
SUPPORTED_LANGUAGES = {
    "🇺🇸 English": {
        "code": "en",
        "name": "English",
        "voice_lang": "en-US",
        "rtl": False
    },
    "🇮🇳 हिंदी (Hindi)": {
        "code": "hi", 
        "name": "हिंदी",
        "voice_lang": "hi-IN",
        "rtl": False
    },
    "🇮🇳 తెలుగు (Telugu)": {
        "code": "te",
        "name": "తెలుగు", 
        "voice_lang": "te-IN",
        "rtl": False
    },
    "🇮🇳 தமிழ் (Tamil)": {
        "code": "ta",
        "name": "தமிழ்",
        "voice_lang": "ta-IN", 
        "rtl": False
    },
    "🇮🇳 ಕನ್ನಡ (Kannada)": {
        "code": "kn",
        "name": "ಕನ್ನಡ",
        "voice_lang": "kn-IN",
        "rtl": False
    },
    "🇮🇳 మరాఠీ (Marathi)": {
        "code": "mr",
        "name": "మరాఠీ", 
        "voice_lang": "mr-IN",
        "rtl": False
    },
    "🇮🇳 বাংলা (Bengali)": {
        "code": "bn",
        "name": "বাংলা",
        "voice_lang": "bn-IN", 
        "rtl": False
    },
    "🇮🇳 ગુજરાતી (Gujarati)": {
        "code": "gu",
        "name": "ગુજરાતી",
        "voice_lang": "gu-IN",
        "rtl": False
    }
}

# UI Text and Hints for each language
LANGUAGE_HINTS = {
    "en": {
        "input_placeholder": "Ask your agriculture question in English...",
        "voice_hint": "Click to speak your question",
        "submit_button": "🔍 Get Answer",
        "loading_text": "🤔 Thinking... Please wait",
        "error_no_input": "⚠️ Please enter a question before submitting.",
        "voice_not_supported": "Voice recognition not supported in this browser. Please use Chrome, Safari, or Edge.",
        "example_questions": [
            "How to increase wheat yield?",
            "Best fertilizer for tomatoes?",
            "When to plant rice?",
            "How to control pests in cotton?"
        ]
    },
    "hi": {
        "input_placeholder": "अपना कृषि प्रश्न हिंदी में पूछें...",
        "voice_hint": "अपना प्रश्न बोलने के लिए क्लिक करें",
        "submit_button": "🔍 उत्तर पाएं",
        "loading_text": "🤔 सोच रहा हूं... कृपया प्रतीक्षा करें",
        "error_no_input": "⚠️ कृपया सबमिट करने से पहले एक प्रश्न दर्ज करें।",
        "voice_not_supported": "इस ब्राउज़र में आवाज पहचान समर्थित नहीं है। कृपया Chrome, Safari, या Edge का उपयोग करें।",
        "example_questions": [
            "गेहूं की पैदावार कैसे बढ़ाएं?",
            "टमाटर के लिए सबसे अच्छा उर्वरक?",
            "चावल कब बोना चाहिए?",
            "कपास में कीटों को कैसे नियंत्रित करें?"
        ]
    },
    "te": {
        "input_placeholder": "మీ వ్యవసాయ ప్రశ్నను తెలుగులో అడగండి...",
        "voice_hint": "మీ ప్రశ్న చెప్పడానికి క్లిక్ చేయండి",
        "submit_button": "🔍 సమాధానం పొందండి",
        "loading_text": "🤔 ఆలోచిస్తున్నాను... దయచేసి వేచి ఉండండి",
        "error_no_input": "⚠️ దయచేసి సబ్మిట్ చేయడానికి ముందు ఒక ప్రశ్న టైప్ చేయండి।",
        "voice_not_supported": "ఈ బ్రౌజర్‌లో వాయిస్ రికగ్నిషన్ మద్దతు లేదు। దయచేసి Chrome, Safari లేదా Edge ఉపయోగించండి।",
        "example_questions": [
            "గోధుమల దిగుబడిని ఎలా పెంచాలి?",
            "టమాటాలకు ఉత్తమ ఎరువు ఏది?",
            "వరిని ఎప్పుడు నాటాలి?",
            "పత్తిలో కీటకాలను ఎలా నియంత్రించాలి?"
        ]
    },
    "ta": {
        "input_placeholder": "உங்கள் விவசாய கேள்வியை தமிழில் கேளுங்கள்...",
        "voice_hint": "உங்கள் கேள்வியைச் சொல்ல கிளிக் செய்யுங்கள்",
        "submit_button": "🔍 பதில் பெறுங்கள்",
        "loading_text": "🤔 யோசித்துக்கொண்டிருக்கிறேன்... தயவுசெய்து காத்திருங்கள்",
        "error_no_input": "⚠️ சமர்ப்பிக்கும் முன் ஒரு கேள்வியை உள்ளிடவும்।",
        "voice_not_supported": "இந்த உலாவியில் குரல் அடையாளம் ஆதரிக்கப்படவில்லை। தயவுசெய்து Chrome, Safari அல்லது Edge ஐப் பயன்படுத்தவும்।",
        "example_questions": [
            "கோதுமை விளைச்சலை எவ்வாறு அதிகரிப்பது?",
            "தக்காளிக்கு சிறந்த உரம் எது?",
            "அரிசி எப்போது நடவேண்டும்?",
            "பருத்தியில் பூச்சிகளை எவ்வாறு கட்டுப்படுத்துவது?"
        ]
    }
}

# UI Theme Configuration
UI_THEME = {
    "primary_color": "#4CAF50",
    "secondary_color": "#2E7D32", 
    "accent_color": "#ff6b6b",
    "background_color": "#f8f9fa",
    "text_color": "#333333",
    "border_radius": "15px",
    "shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
}

# Voice Recognition Settings
VOICE_CONFIG = {
    "continuous": os.getenv("VOICE_CONTINUOUS", "false").lower() == "true",
    "interim_results": os.getenv("VOICE_INTERIM_RESULTS", "false").lower() == "true",
    "max_alternatives": int(os.getenv("VOICE_MAX_ALTERNATIVES", "1")),
    "timeout": int(os.getenv("VOICE_TIMEOUT", "10")),  # seconds
    "phrase_time_limit": int(os.getenv("VOICE_PHRASE_TIME_LIMIT", "30"))  # seconds
}

# Response Configuration
RESPONSE_CONFIG = {
    "max_answer_length": 1000,
    "show_confidence": True,
    "show_source": True,
    "enable_followup": True
}

# Chat History Configuration
HISTORY_CONFIG = {
    "max_items": 20,
    "display_items": 5,
    "enable_export": True,
    "auto_save": True
}

ERROR_MESSAGES = {
    "en": {
        "connection_error": "Could not connect to the server. Please ensure the backend is running.",
        "timeout_error": "The server took too long to respond. Please try again.",
        "general_error": "An unexpected error occurred. Please try again later."
    },
    "hi": {
        "connection_error": "सर्वर से कनेक्ट नहीं हो सका। कृपया सुनिश्चित करें कि बैकएंड चल रहा है।",
        "timeout_error": "सर्वर को जवाब देने में बहुत समय लगा। कृपया पुनः प्रयास करें।",
        "general_error": "एक अप्रत्याशित त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।"
    },
    # Add more languages as needed
}

# Sample Questions for different languages
SAMPLE_QUESTIONS = {
    "en": [
        "How to increase wheat yield?",
        "Best fertilizer for tomatoes?", 
        "When to plant rice?",
        "How to control pests in cotton?",
        "What are the symptoms of crop diseases?",
        "How to improve soil fertility?",
        "Best irrigation methods for vegetables?",
        "How to store harvested grains?"
    ],
    "hi": [
        "गेहूं की पैदावार कैसे बढ़ाएं?",
        "टमाटर के लिए सबसे अच्छा उर्वरक?",
        "चावल कब बोना चाहिए?", 
        "कपास में कीटों को कैसे नियंत्रित करें?",
        "फसल की बीमारियों के लक्षण क्या हैं?",
        "मिट्टी की उर्वरता कैसे सुधारें?",
        "सब्जियों के लिए सबसे अच्छी सिंचाई विधि?",
        "कटाई के बाद अनाज को कैसे स्टोर करें?"
    ],
    "te": [
        "గోధుమల దిగుబడిని ఎలా పెంచాలి?",
        "టమాటాలకు ఉత్తమ ఎరువు ఏది?",
        "వరిని ఎప్పుడు నాటాలి?",
        "పత్తిలో కీటకాలను ఎలా నియంత్రించాలి?",
        "పంట వ్యాధుల లక్షణాలు ఏమిటి?",
        "నేల సారవంతతను ఎలా మెరుగుపరచాలి?",
        "కూరగాయలకు ఉత్తమ నీటిపారుదల పద్ధతులు?",
        "కోత తర్వాత ధాన్యాలను ఎలా నిల్వ చేయాలి?"
    ],
    "ta": [
        "கோதுமை விளைச்சலை எவ்வாறு அதிகரிப்பது?",
        "தக்காளிக்கு சிறந்த உரம் எது?",
        "அரிசி எப்போது நடவேண்டும்?", 
        "பருத்தியில் பூச்சிகளை எவ்வாறு கட்டுப்படுத்துவது?",
        "பயிர் நோய்களின் அறிகுறிகள் என்னவென்று?",
        "மண் வளத்தை எவ்வாறு மேம்படுத்துவது?",
        "காய்கறிகளுக்கான சிறந்த நீர்ப்பாசன முறைகள்?",
        "அறுவடைக்குப் பிறகு தானியங்களை எவ்வாறு சேமிப்பது?"
    ]
}

# Development Configuration
DEV_CONFIG = {
    "debug_mode": os.getenv("DEBUG", "False").lower() == "true",
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "enable_mock_api": os.getenv("ENABLE_MOCK_API", "False").lower() == "true"
}