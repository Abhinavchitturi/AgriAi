# 🚀 Quick Start Guide - AgriAI Assistant UI

Get your AgriAI Assistant running in just a few minutes!

## ⚡ Option 1: Instant Setup (Recommended)

### Step 1: Clone & Install
```bash
# Clone the repository
git clone <your-repo-url>
cd agri-ai-assistant-ui

# Quick setup with the run script
python run.py --mock-api
```

That's it! 🎉 The app will open in your browser at `http://localhost:8501`

---

## 🐍 Option 2: Manual Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the App
```bash
streamlit run app.py
```

### Step 3: Open Browser
Navigate to `http://localhost:8501`

---

## 🧪 Option 3: Test First

### Run Tests to Verify Everything Works
```bash
python test_ui.py
```

### Run the App
```bash
python run.py
```

---

## 🌐 First Time Usage

1. **Choose Language**: Select your preferred language from the dropdown
2. **Ask Question**: Type an agriculture question like:
   - "How to increase wheat yield?"
   - "Best fertilizer for tomatoes?"
   - "गेहूं की खेती कैसे करें?" (Hindi)
3. **Get Answer**: Click "🔍 Get Answer" and see the AI response
4. **Try Voice**: Click 🎤 to ask questions using your voice (Chrome/Safari/Edge)

---

## 🔧 Configuration Options

### Basic Configuration
```bash
# Custom API URL
python run.py --api-url http://your-backend-api.com

# Custom port
python run.py --port 8502

# Debug mode
python run.py --debug
```

### Advanced Configuration
1. Copy `config_example.py` to `local_config.py`
2. Modify settings as needed
3. Restart the app

---

## 🐳 Docker Quick Start

### Build & Run
```bash
docker build -t agri-ai-ui .
docker run -p 8501:8501 agri-ai-ui
```

### With Custom API
```bash
docker run -p 8501:8501 -e API_BASE_URL=http://your-api.com agri-ai-ui
```

---

## 📱 Mobile Testing

1. **Find your IP address**:
   ```bash
   # On Windows
   ipconfig
   
   # On Mac/Linux  
   ifconfig
   ```

2. **Run with network access**:
   ```bash
   python run.py --host 0.0.0.0
   ```

3. **Access from mobile**: `http://YOUR_IP:8501`

---

## 🆘 Troubleshooting

### Common Issues & Solutions

**🔴 "Module not found" error**
```bash
pip install --upgrade -r requirements.txt
```

**🔴 Port already in use**
```bash
python run.py --port 8502
```

**🔴 Voice input not working**
- Use Chrome, Safari, or Edge browser
- Ensure HTTPS for production (HTTP is ok for localhost)
- Allow microphone permissions

**🔴 API connection failed**
```bash
# Use mock API for testing
python run.py --mock-api
```

**🔴 Slow performance**
- Check your internet connection
- Use mock API for development
- Ensure backend API is running

---

## 📚 Sample Questions to Try

### English
- "How to increase crop yield?"
- "Best fertilizer for rice?"
- "When to plant tomatoes?"
- "How to control pests naturally?"

### Hindi (हिंदी)
- "फसल की पैदावार कैसे बढ़ाएं?"
- "चावल के लिए सबसे अच्छा उर्वरक?"
- "टमाटर कब लगाना चाहिए?"

### Telugu (తెలుగు)
- "పంట దిగుబడిని ఎలా పెంచాలి?"
- "వరికి ఉత్తమ ఎరువు ఏది?"
- "టమాటాలను ఎప్పుడు నాటాలి?"

### Tamil (தமிழ்)
- "பயிர் விளைச்சலை எவ்வாறு அதிகரிப்பது?"
- "அரிசிக்கு சிறந்த உரம் எது?"
- "தக்காளி எப்போது நடவேண்டும்?"

---

## 🛠 Development Mode

### Enable Development Features
```bash
python run.py --debug --mock-api
```

### Hot Reload
Streamlit automatically reloads when you modify files. Just save and refresh!

### View Logs
```bash
streamlit run app.py --logger.level debug
```

---

## 🚀 Deployment Quick Start

### Deploy to Streamlit Cloud
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository and deploy `app.py`

### Deploy with Docker
```bash
python deploy.py docker
```

### Deploy to Heroku
```bash
python deploy.py heroku --app-name your-app-name
```

---

## 🎯 Next Steps

1. **🔗 Connect Real Backend**: Replace mock API with your FastAPI backend
2. **🎨 Customize**: Modify `config.py` for your branding
3. **🌍 Add Languages**: Extend `SUPPORTED_LANGUAGES` in config
4. **📊 Analytics**: Enable usage tracking in configuration
5. **🔒 Security**: Add authentication for production use

---

## 💡 Pro Tips

- **🎤 Voice works best** on mobile Chrome/Safari
- **📱 Mobile-optimized** - test on actual devices
- **🌍 Multilingual** - switch languages anytime
- **💾 History saved** - view past conversations
- **⚡ Fast responses** with mock API for development
- **🔧 Configurable** - check `config_example.py` for options

---

## 📞 Need Help?

- **🐛 Found a bug?** Check the logs in browser console
- **❓ Have questions?** Review the full README.md
- **🧪 Test issues?** Run `python test_ui.py`
- **🔧 Configuration help?** See `config_example.py`

---

## 🎉 You're Ready!

Your AgriAI Assistant is now running! 

**🌾 Happy farming! 🚜**

---

*Built with ❤️ for farmers and agricultural communities worldwide*