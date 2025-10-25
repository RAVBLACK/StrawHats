# 🛡️ SentiGuard - AI-Powered Mental Health Monitoring System

<div align="center">

![SentiGuard Logo](https://img.shields.io/badge/SentiGuard-Mental%20Health%20Guardian-blue?style=for-the-badge&logo=shield)

**Your Silent Digital Mental Health Guardian**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=flat-square)]()

*Because mental health shouldn't be a silent struggle.*

</div>

---

## 🌟 Overview

SentiGuard is an innovative **AI-powered desktop application** that passively monitors your digital interactions to understand your mental wellness patterns. It combines advanced sentiment analysis, voice emotion detection, and AI companionship to provide early warning systems for mental health concerns while maintaining complete privacy.

### 🎯 Key Mission
- **Early Detection**: Identify mental health concerns before they escalate
- **Privacy-First**: All processing happens locally on your device
- **Proactive Support**: AI companion provides contextual mental health guidance
- **Guardian Alerts**: Automatically notify trusted contacts during concerning periods

---

## ✨ Features

### 🧠 **Advanced Sentiment Analysis**
- **Context-Aware AI**: Understanding sarcasm, idioms, and cultural nuances
- **Enhanced VADER**: Custom algorithms that go beyond basic sentiment analysis
- **Real-time Processing**: Instant mood detection as you type
- **Pattern Recognition**: Identifies concerning behavioral trends

### 🎤 **Voice Emotion Detection**
- **Multi-modal Analysis**: Text + Voice + Behavioral patterns
- **Audio Feature Extraction**: Pitch, tone, rhythm, and energy analysis
- **Real-time Voice Processing**: Live sentiment analysis during speech
- **Emotion Fingerprinting**: Advanced voice emotion recognition

### 🤖 **AI Companion**
- **Google Gemini Integration**: Conversational support with mood awareness
- **Personalized Insights**: Context-aware mental health suggestions
- **24/7 Availability**: Always-on emotional support
- **Privacy-Focused**: Conversations stay on your device

### 📊 **Dynamic Visualization**
- **Live Mood Dashboard**: Beautiful, real-time mood visualization
- **Trend Analytics**: Track mental wellness patterns over time
- **Interactive Charts**: Matplotlib-powered mood trend analysis
- **Enhanced Mood Backgrounds**: Visual feedback that reflects your emotional state

### 🚨 **Guardian Alert System**
- **Smart Detection**: Identifies sustained negative sentiment patterns
- **Automated Notifications**: Emails trusted contacts when help may be needed
- **Customizable Thresholds**: Adjustable sensitivity for alert triggers
- **Privacy-Respectful**: Alerts contain no personal content, just care suggestions

### 🔒 **Privacy & Security**
- **100% Local Processing**: Your data never leaves your computer
- **Auto-Cleanup**: Sensitive data automatically cleared on app exit
- **Google OAuth**: Secure authentication without password storage
- **GDPR Compliant**: You control all your mental health data

---

## 🏗️ Architecture

### **Core Components**

#### 📁 **Main Application**
- **`main.py`** - Application entry point with cleanup and signal handling
- **`gui.py`** - Modern Tkinter-based user interface (2,267 lines of advanced GUI)
- **`auth.py`** - Google OAuth authentication system

#### 🔍 **Analysis Engine**
- **`analyzer.py`** - Core sentiment analysis with VADER integration
- **`enhanced_analyzer.py`** - Advanced context-aware sentiment analysis
- **`audio_emotion_analyzer.py`** - Voice emotion detection and analysis

#### 📡 **Data Collection**
- **`keylogger.py`** - Privacy-focused keystroke monitoring
- **`voice_recorder.py`** - Real-time voice recording and processing

#### 🤖 **AI & Intelligence**
- **`ai_companion.py`** - Google Gemini-powered conversational AI
- **`personalized_insights.py`** - AI-generated mental health insights

#### 🎨 **Visualization**
- **`enhanced_mood_bg.py`** - Dynamic mood-responsive backgrounds
- **`mood_background.py`** - Base mood visualization system

#### 📧 **Communication**
- **`mailer.py`** - Email alert system for guardian notifications

---

## 🚀 Installation

### **Prerequisites**
- **Python 3.9+** (3.11+ recommended)
- **Windows 10/11** (primary support)
- **Microphone** (optional, for voice features)
- **Google Account** (for OAuth authentication)

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/yourusername/sentiguard.git
cd sentiguard
```

### **Step 2: Create Virtual Environment**
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Note for Windows users**: If PyAudio installation fails:
```bash
pip install pipwin
pipwin install pyaudio
```

### **Step 4: Google OAuth Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Configure OAuth consent screen (External)
5. Create OAuth Client ID → Choose "Desktop app"
6. Download credentials and save as `client_secret.json`

### **Step 5: AI Companion Setup (Optional)**
1. Get a [Google Gemini API key](https://aistudio.google.com/app/apikey)
2. Create `.env` file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### **Step 6: Email Configuration (Optional)**
1. Copy `email_config.json.template` to `email_config.json`
2. Update with your email settings for guardian alerts

---

## 🎮 Usage

### **Quick Start**
```bash
python main.py
```

### **First Launch**
1. **Google Authentication**: Browser will open for OAuth login
2. **Microphone Setup**: Grant microphone permissions if prompted
3. **Guardian Email**: Set up trusted contact for alerts
4. **Start Monitoring**: Application begins passive monitoring

### **Main Interface**

#### **📊 Dashboard**
- **Real-time Mood Chart**: Live sentiment visualization
- **Mood History**: Track patterns over time
- **Current Status**: Instant mood feedback

#### **🎤 Voice Recording**
- **Start/Stop Recording**: Toggle voice emotion analysis
- **Real-time Transcription**: See what's being analyzed
- **Voice Sentiment**: Live voice emotion detection

#### **🤖 AI Chat**
- **Conversational Support**: Chat with mood-aware AI
- **Personalized Insights**: Get contextual mental health tips
- **24/7 Availability**: Always-on emotional support

#### **⚙️ Settings**
- **Guardian Email**: Configure trusted contact
- **Alert Sensitivity**: Adjust detection thresholds
- **Privacy Controls**: Manage data retention
- **Theme Options**: Light/Dark mode

---

## 📚 Dependencies

### **Core Libraries**
```python
# Sentiment Analysis
nltk>=3.8.1                    # Natural language processing
numpy>=1.26.4                  # Numerical computing
scipy>=1.11.4                  # Scientific computing

# Voice Processing
SpeechRecognition>=3.10.0      # Speech-to-text
pyaudio>=0.2.14               # Audio capture
librosa>=0.10.2               # Audio analysis
soundfile>=0.12.1             # Audio file handling

# GUI & Visualization
matplotlib>=3.8.0             # Plotting and charts
pillow>=10.3.0                # Image processing
tkinter                       # GUI framework (built-in)

# Authentication & APIs
google-auth-oauthlib>=1.2.0   # Google OAuth
google-api-python-client>=2.131.0  # Google API client
google-generativeai>=0.8.0   # Gemini AI

# System Integration
pynput>=1.7.7                 # Keyboard monitoring
python-dotenv>=1.0.0          # Environment variables
requests>=2.31.0              # HTTP requests

# Performance
numba>=0.60.0                 # JIT compilation for audio processing
```

---

## 🔧 Configuration

### **Environment Variables (.env)**
```bash
# AI Companion
GEMINI_API_KEY=your_gemini_api_key

# Optional: Custom API endpoints
CUSTOM_API_ENDPOINT=your_custom_endpoint
```

### **Email Configuration (email_config.json)**
```json
{
    "from_addr": "your_email@gmail.com",
    "app_password": "your_app_password",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465
}
```

### **User Settings (auto-generated)**
```json
{
    "guardian_email": "trusted@contact.com",
    "alert_threshold": -0.5,
    "alert_limit": 5,
    "theme": "dark",
    "voice_enabled": true
}
```

---

## 🛡️ Privacy & Security

### **Data Protection**
- ✅ **Local Processing Only**: No data sent to external servers
- ✅ **Auto-Cleanup**: Keystrokes cleared on app exit
- ✅ **Minimal Data Storage**: Only anonymized mood scores saved
- ✅ **User Control**: Complete control over data retention

### **Security Features**
- ✅ **Google OAuth**: Industry-standard authentication
- ✅ **No Password Storage**: Secure token-based authentication
- ✅ **Encrypted Communication**: HTTPS for all external calls
- ✅ **GDPR Compliant**: Privacy by design

### **What's Stored vs. What's Cleared**

#### **Preserved (Anonymous Analytics)**
- Mood scores with timestamps
- General usage statistics
- Alert frequency (no content)

#### **Auto-Cleared (Privacy Protection)**
- Actual keystroke content
- Voice transcriptions
- Alert details
- Temporary cache files

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### **Development Setup**
```bash
# Fork the repository
git clone https://github.com/yourusername/sentiguard.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
python main.py

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

### **Contribution Guidelines**
- Follow PEP 8 style guidelines
- Add comments for complex algorithms
- Test all features before submitting
- Update documentation for new features
- Respect privacy-first principles

---

## 🐛 Troubleshooting

### **Common Issues**

#### **PyAudio Installation Error**
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# Linux
sudo apt-get install portaudio19-dev python3-dev
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio
```

#### **Microphone Not Working**
1. Check Windows microphone permissions
2. Ensure no other app is using microphone
3. Try running as administrator

#### **Google OAuth Error**
1. Verify `client_secret.json` is in project root
2. Check OAuth consent screen configuration
3. Ensure redirect URI matches settings

#### **AI Companion Not Available**
1. Verify `GEMINI_API_KEY` in `.env` file
2. Check API key validity
3. Ensure `python-dotenv` is installed

---

## 📈 Roadmap

### **v2.0 - Enhanced Intelligence**
- [ ] Multi-language sentiment analysis
- [ ] Advanced voice emotion models
- [ ] Cross-platform support (macOS, Linux)
- [ ] Mobile companion app

### **v3.0 - Community Features**
- [ ] Anonymous peer support networks
- [ ] Mental health resource integration
- [ ] Professional therapist connections
- [ ] Research contribution options

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

### **Getting Help**
- 📖 [Documentation](docs/)
- 💬 [Discussions](https://github.com/yourusername/sentiguard/discussions)
- 🐛 [Issue Tracker](https://github.com/yourusername/sentiguard/issues)
- 📧 [Email Support](mailto:support@sentiguard.com)

### **Mental Health Resources**
- 🇺🇸 **Crisis Hotline**: 988 (Suicide & Crisis Lifeline)
- 🌍 **International**: [befrienders.org](https://befrienders.org)
- 💬 **Crisis Text Line**: Text HOME to 741741

---

## 🌍 United Nations SDG Alignment

### **Primary: SDG 3 - Good Health and Well-being**
**Target 3.4**: "By 2030, reduce by one third premature mortality from non-communicable diseases through prevention and treatment and promote mental health and well-being"

**How SentiGuard Contributes**:
- ✅ **Early Detection**: Identifies mental health concerns before crisis
- ✅ **Prevention-Focused**: Shifts from reactive to proactive care
- ✅ **Accessibility**: 24/7 mental health monitoring
- ✅ **Data-Driven**: Evidence-based wellness tracking

### **Secondary Alignments**:
- **SDG 4** (Quality Education): Student mental wellness support
- **SDG 8** (Decent Work): Workplace mental health monitoring
- **SDG 10** (Reduced Inequalities): Universal access to mental health tools

---

## 🙏 Acknowledgments

- **NLTK Team** - Natural language processing foundation
- **Google** - Gemini AI and OAuth services
- **Python Community** - Amazing ecosystem of libraries
- **Mental Health Advocates** - Inspiration and guidance
- **Open Source Contributors** - Making mental health tech accessible

---

## ⚠️ Disclaimer

**SentiGuard is a wellness monitoring tool and not a replacement for professional mental health care.** Always consult qualified mental health professionals for clinical advice. If you're experiencing a mental health emergency, contact your local emergency services immediately.

---

<div align="center">

**🛡️ SentiGuard - Technology for Humanity**

*Advancing SDG 3 through innovative mental health prevention*

[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-red.svg?style=flat-square)]()
[![Privacy First](https://img.shields.io/badge/Privacy-First-green.svg?style=flat-square)]()
[![Mental Health](https://img.shields.io/badge/Mental%20Health-Matters-blue.svg?style=flat-square)]()

</div>
