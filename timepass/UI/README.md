# 🌾 AgriAI Assistant UI

A multilingual, mobile-friendly Streamlit application for agricultural queries and assistance. Built for farmers and agri-stakeholders to easily access AI-powered agricultural information.

## ✨ Features

- **🌐 Multilingual Support**: English, Hindi, Telugu, Tamil, Kannada, Marathi, Bengali, Gujarati
- **🎤 Voice Input**: Web Speech API integration for voice queries
- **📱 Mobile-Friendly**: Responsive design optimized for mobile devices
- **💬 Chat History**: Track and export previous conversations  
- **🔗 API Integration**: Connects to FastAPI backend for AI responses
- **⚡ Fast & Lightweight**: Built with Streamlit for quick deployment
- **🎨 Clean UI**: Farmer-friendly interface with large fonts and clear layout

## 🏗 Architecture

```
Frontend (Streamlit) ↔ REST API ↔ Backend (FastAPI) ↔ AI Model
```

### Components

| Component | Description |
|-----------|-------------|
| `app.py` | Main Streamlit application |
| `config.py` | Configuration and language settings |
| `api_client.py` | Backend API communication |
| `utils.py` | Utility functions and helpers |

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agri-ai-assistant-ui
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   # Create .env file for custom configuration
   echo "API_BASE_URL=http://localhost:8000" > .env
   echo "DEBUG=True" >> .env
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**
   - Navigate to `http://localhost:8501`
   - The app will automatically open in your default browser

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Backend API URL |
| `API_TIMEOUT` | `30` | Request timeout in seconds |
| `DEBUG` | `False` | Enable debug mode |
| `ENABLE_MOCK_API` | `False` | Use mock API for testing |

### Language Configuration

Edit `config.py` to modify:
- Supported languages
- UI text translations
- Sample questions
- Error messages

## 🎯 Usage

### Basic Flow

1. **Select Language**: Choose your preferred language from dropdown
2. **Ask Question**: 
   - Type your agriculture question, OR
   - Click 🎤 to use voice input
3. **Get Answer**: Click "Get Answer" to submit
4. **View Response**: See AI response with source information
5. **Check History**: Expand "Recent Conversations" to see past queries

### Voice Input

- **Supported Browsers**: Chrome, Safari, Edge (with Web Speech API)
- **Languages**: Supports voice recognition in multiple Indian languages
- **Usage**: Click 🎤 button and speak clearly into microphone

### Sample Questions

**English:**
- "How to increase wheat yield?"
- "Best fertilizer for tomatoes?"
- "When to plant rice?"

**Hindi:**
- "गेहूं की पैदावार कैसे बढ़ाएं?"
- "टमाटर के लिए सबसे अच्छा उर्वरक?"

**Telugu:**
- "గోధుమల దిగుబడిని ఎలా పెంచాలి?"
- "టమాటాలకు ఉత్తమ ఎరువు ఏది?"

## 🔧 API Integration

### Backend Requirements

The UI expects a FastAPI backend with these endpoints:

```python
POST /query
{
  "query": "How to increase crop yield?",
  "language": "en",
  "timestamp": "2024-01-15T10:30:00",
  "user_id": "optional"
}

Response:
{
  "answer": "To increase crop yield...",
  "source": "Agricultural Research DB",
  "confidence": 0.85,
  "timestamp": "2024-01-15T10:30:05"
}
```

```python
GET /history?limit=20
GET /health
GET /languages
```

### Mock API Mode

For development without backend:

```bash
export ENABLE_MOCK_API=True
streamlit run app.py
```

## 📱 Mobile Optimization

### Features
- **Responsive Design**: Adapts to screen sizes
- **Large Touch Targets**: Easy-to-tap buttons
- **Optimized Fonts**: Readable text on small screens
- **Minimal Scrolling**: Compact layout
- **Voice-First**: Reduces typing on mobile

### Testing Mobile
- Use browser dev tools to test responsive design
- Test on actual mobile devices for best experience
- Voice input works best on mobile Chrome/Safari

## 🎨 Customization

### Styling

Edit CSS in `app.py` → `load_css()` function:

```python
def load_css():
    st.markdown("""
    <style>
    /* Modify colors, fonts, layout */
    .header {
        background: your-gradient;
    }
    </style>
    """, unsafe_allow_html=True)
```

### Adding Languages

1. **Update `config.py`**:
   ```python
   SUPPORTED_LANGUAGES["🇮🇳 ಕನ್ನಡ (Kannada)"] = {
       "code": "kn",
       "name": "ಕನ್ನಡ",
       "voice_lang": "kn-IN"
   }
   ```

2. **Add translations**:
   ```python
   LANGUAGE_HINTS["kn"] = {
       "input_placeholder": "ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ..."
   }
   ```

## 🧪 Development

### Project Structure
```
agri-ai-assistant-ui/
├── app.py              # Main Streamlit app
├── config.py           # Configuration settings
├── api_client.py       # API communication
├── utils.py           # Utility functions
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── .env               # Environment variables (optional)
```

### Testing

```bash
# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black *.py

# Lint code
flake8 *.py
```

### Mock Development

Set `ENABLE_MOCK_API=True` to develop without backend:
- Uses `MockAgriAIClient` for responses
- Simulates API delays and responses
- Perfect for UI development and testing

## 🚀 Deployment

### Local Deployment
```bash
streamlit run app.py --server.port 8501
```

### Cloud Deployment

**Streamlit Cloud:**
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Set environment variables in Streamlit Cloud dashboard

**Docker:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

**Heroku:**
```bash
# Add Procfile
echo "web: streamlit run app.py --server.port \$PORT" > Procfile
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to functions
- Test on multiple screen sizes
- Ensure multilingual compatibility
- Optimize for low-bandwidth scenarios

## 📋 Roadmap

- [ ] **Enhanced Voice**: Better voice recognition accuracy
- [ ] **Offline Mode**: Cached responses for common queries
- [ ] **Image Upload**: Visual crop disease identification
- [ ] **Location Services**: Localized weather and crop advice
- [ ] **Push Notifications**: Timely farming reminders
- [ ] **Dark Mode**: Eye-friendly dark theme
- [ ] **Export Features**: PDF/Word export of conversations

## 🆘 Troubleshooting

### Common Issues

**Voice Input Not Working:**
- Ensure HTTPS connection (required for microphone access)
- Use supported browsers (Chrome, Safari, Edge)
- Check microphone permissions

**API Connection Failed:**
- Verify backend is running on correct port
- Check `API_BASE_URL` in configuration
- Enable mock mode for offline development

**Layout Issues on Mobile:**
- Clear browser cache
- Test in mobile browser (not just dev tools)
- Check CSS media queries

**Language Display Issues:**
- Ensure proper font support for Indic scripts
- Check character encoding (UTF-8)
- Verify language codes in configuration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit Team**: For the amazing framework
- **Agricultural Experts**: For domain knowledge and guidance
- **Open Source Community**: For tools and libraries used
- **Farmers**: The end users who inspire this work

---

Built with ❤️ for farmers and agricultural communities worldwide 🌾