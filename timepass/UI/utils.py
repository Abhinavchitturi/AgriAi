"""
Utility functions for AgriAI Assistant UI
Contains helper functions for various operations
"""

import streamlit as st
import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import base64
from io import BytesIO

def format_timestamp(timestamp: str) -> str:
    """
    Format timestamp for display
    
    Args:
        timestamp: ISO format timestamp string
        
    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Unknown time"

def clean_text(text: str) -> str:
    """
    Clean and normalize text input
    
    Args:
        text: Raw text input
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\.\?\!,;:\'\"-]', '', text)
    
    return text

def truncate_text(text: str, max_length: int = 150, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix

def highlight_keywords(text: str, keywords: List[str]) -> str:
    """
    Highlight keywords in text using HTML
    
    Args:
        text: Text to process
        keywords: List of keywords to highlight
        
    Returns:
        Text with highlighted keywords
    """
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f'<mark style="background-color: #fff3cd; padding: 1px 3px; border-radius: 3px;">{keyword}</mark>', text)
    
    return text

def extract_language_from_text(text: str) -> str:
    """
    Detect language from text (basic detection)
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code (en, hi, te, ta, etc.)
    """
    # Simple regex-based detection for Indian languages
    if re.search(r'[\u0900-\u097F]', text):  # Devanagari (Hindi, Marathi)
        return 'hi'
    elif re.search(r'[\u0C00-\u0C7F]', text):  # Telugu
        return 'te'
    elif re.search(r'[\u0B80-\u0BFF]', text):  # Tamil
        return 'ta'
    elif re.search(r'[\u0C80-\u0CFF]', text):  # Kannada
        return 'kn'
    elif re.search(r'[\u0A80-\u0AFF]', text):  # Gujarati
        return 'gu'
    elif re.search(r'[\u0980-\u09FF]', text):  # Bengali
        return 'bn'
    else:
        return 'en'  # Default to English

def validate_query(query: str, min_length: int = 3, max_length: int = 500) -> Tuple[bool, str]:
    """
    Validate user query
    
    Args:
        query: Query text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Please enter a question."
    
    query = query.strip()
    
    if len(query) < min_length:
        return False, f"Question is too short. Please enter at least {min_length} characters."
    
    if len(query) > max_length:
        return False, f"Question is too long. Please keep it under {max_length} characters."
    
    # Check for spam or repetitive content
    if len(set(query.lower().split())) < len(query.split()) // 3:
        return False, "Please enter a meaningful question without repetitive words."
    
    return True, ""

def generate_session_id() -> str:
    """
    Generate a unique session ID
    
    Returns:
        Session ID string
    """
    import uuid
    return str(uuid.uuid4())

def save_to_local_storage(key: str, data: Any) -> bool:
    """
    Save data to Streamlit session state (local storage simulation)
    
    Args:
        key: Storage key
        data: Data to save
        
    Returns:
        True if saved successfully
    """
    try:
        st.session_state[f"storage_{key}"] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        return True
    except Exception as e:
        st.error(f"Failed to save data: {e}")
        return False

def load_from_local_storage(key: str, default: Any = None) -> Any:
    """
    Load data from Streamlit session state
    
    Args:
        key: Storage key
        default: Default value if key not found
        
    Returns:
        Stored data or default value
    """
    try:
        storage_key = f"storage_{key}"
        if storage_key in st.session_state:
            return st.session_state[storage_key]["data"]
        return default
    except Exception:
        return default

def format_confidence_score(confidence: float) -> str:
    """
    Format confidence score for display
    
    Args:
        confidence: Confidence value (0.0 to 1.0)
        
    Returns:
        Formatted confidence string
    """
    if confidence >= 0.9:
        return f"🟢 {confidence:.1%} (Very High)"
    elif confidence >= 0.7:
        return f"🟡 {confidence:.1%} (High)"
    elif confidence >= 0.5:
        return f"🟠 {confidence:.1%} (Medium)"
    else:
        return f"🔴 {confidence:.1%} (Low)"

def create_download_link(data: str, filename: str, text: str = "Download") -> str:
    """
    Create a download link for text data
    
    Args:
        data: Data to download
        filename: Suggested filename
        text: Link text
        
    Returns:
        HTML download link
    """
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

def export_chat_history(history: List[Dict[str, Any]], format_type: str = "txt") -> str:
    """
    Export chat history in specified format
    
    Args:
        history: List of chat entries
        format_type: Export format (txt, json, csv)
        
    Returns:
        Formatted export string
    """
    if format_type == "json":
        return json.dumps(history, indent=2, ensure_ascii=False)
    
    elif format_type == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Query", "Answer", "Language", "Source", "Confidence"])
        
        for chat in history:
            writer.writerow([
                chat.get("timestamp", ""),
                chat.get("query", ""),
                chat.get("answer", ""),
                chat.get("language", ""),
                chat.get("source", ""),
                chat.get("confidence", "")
            ])
        
        return output.getvalue()
    
    else:  # txt format
        output = []
        output.append("AgriAI Assistant - Chat History")
        output.append("=" * 40)
        output.append("")
        
        for i, chat in enumerate(history, 1):
            output.append(f"Conversation #{i}")
            output.append(f"Time: {chat.get('timestamp', 'Unknown')}")
            output.append(f"Language: {chat.get('language', 'Unknown')}")
            output.append(f"Question: {chat.get('query', '')}")
            output.append(f"Answer: {chat.get('answer', '')}")
            output.append(f"Source: {chat.get('source', '')}")
            output.append(f"Confidence: {chat.get('confidence', 'N/A')}")
            output.append("-" * 40)
            output.append("")
        
        return "\n".join(output)

def get_query_suggestions(language: str = "en") -> List[str]:
    """
    Get sample query suggestions based on language
    
    Args:
        language: Language code
        
    Returns:
        List of suggested queries
    """
    from config import SAMPLE_QUESTIONS
    return SAMPLE_QUESTIONS.get(language, SAMPLE_QUESTIONS["en"])

def format_source_info(source: str, confidence: Optional[float] = None) -> str:
    """
    Format source information for display
    
    Args:
        source: Source description
        confidence: Optional confidence score
        
    Returns:
        Formatted source string
    """
    formatted = f"📌 **Source:** {source}"
    
    if confidence is not None:
        confidence_str = format_confidence_score(confidence)
        formatted += f"\n🎯 **Reliability:** {confidence_str}"
    
    return formatted

def create_voice_input_js(language_code: str = "en-US") -> str:
    """
    Generate JavaScript for voice input functionality
    
    Args:
        language_code: Language code for speech recognition
        
    Returns:
        JavaScript code as string
    """
    return f"""
    <script>
    let recognition = null;
    let isListening = false;
    
    function initVoiceRecognition() {{
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = '{language_code}';
            recognition.maxAlternatives = 1;
            
            recognition.onstart = function() {{
                isListening = true;
                updateVoiceButton(true);
            }};
            
            recognition.onresult = function(event) {{
                const transcript = event.results[0][0].transcript;
                document.querySelector('textarea').value = transcript;
                
                // Trigger input event to update Streamlit
                const inputEvent = new Event('input', {{ bubbles: true }});
                document.querySelector('textarea').dispatchEvent(inputEvent);
            }};
            
            recognition.onerror = function(event) {{
                console.error('Speech recognition error:', event.error);
                alert('Voice recognition error: ' + event.error);
                isListening = false;
                updateVoiceButton(false);
            }};
            
            recognition.onend = function() {{
                isListening = false;
                updateVoiceButton(false);
            }};
            
            return true;
        }}
        return false;
    }}
    
    function toggleVoiceRecognition() {{
        if (!recognition && !initVoiceRecognition()) {{
            alert('Voice recognition not supported in this browser. Please use Chrome, Safari, or Edge.');
            return;
        }}
        
        if (isListening) {{
            recognition.stop();
        }} else {{
            recognition.start();
        }}
    }}
    
    function updateVoiceButton(listening) {{
        const button = document.getElementById('voiceBtn');
        if (button) {{
            button.innerHTML = listening ? '🔊' : '🎤';
            button.style.background = listening ? 
                'linear-gradient(90deg, #4CAF50 0%, #45a049 100%)' : 
                'linear-gradient(90deg, #ff6b6b 0%, #ee5a52 100%)';
            button.title = listening ? 'Stop listening' : 'Start voice input';
        }}
    }}
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {{
        initVoiceRecognition();
    }});
    </script>
    """

def check_mobile_device() -> bool:
    """
    Check if user is on a mobile device (basic detection)
    
    Returns:
        True if likely mobile device
    """
    try:
        import streamlit.components.v1 as components
        
        # This is a simplified check - in a real app you might use JavaScript
        # to detect mobile devices more accurately
        return False  # Placeholder
    except:
        return False

def format_mobile_layout(content: str) -> str:
    """
    Format content for mobile-friendly display
    
    Args:
        content: Content to format
        
    Returns:
        Mobile-optimized content
    """
    # Add mobile-specific CSS classes and formatting
    mobile_css = """
    <style>
    @media (max-width: 768px) {
        .mobile-text {
            font-size: 16px !important;
            line-height: 1.5 !important;
        }
        .mobile-button {
            padding: 12px !important;
            font-size: 18px !important;
        }
    }
    </style>
    """
    
    return mobile_css + f'<div class="mobile-text">{content}</div>'

def create_error_message(error_type: str, language: str = "en") -> str:
    """
    Create localized error message
    
    Args:
        error_type: Type of error
        language: Language code
        
    Returns:
        Localized error message
    """
    from config import ERROR_MESSAGES
    
    messages = ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])
    return messages.get(error_type, messages["general_error"])

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename[:100]  # Limit length