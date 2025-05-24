# 🎵 Music Recommendation System v5.0

A comprehensive AI-powered music recommendation system that analyzes your Last.fm listening history to generate personalized playlists and integrate seamlessly with Roon audio systems.

## ✨ New in v5.0: Beautiful Web Interface!

**Say goodbye to the terminal!** 🎉 Now featuring a gorgeous, modern web interface built with Streamlit:

### 🌟 Web Features
- **📊 Interactive Dashboard** - Beautiful visualizations of your music data
- **🎯 Smart Recommendations** - Drag-and-drop playlist generation with AI insights
- **🎵 Roon Integration** - Direct control of your high-end audio system
- **📱 Mobile-Friendly** - Responsive design that works on all devices
- **💾 Export Options** - Download playlists in CSV, JSON, and M3U formats

### 🚀 Quick Start with Web Interface

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the beautiful web app
python launch_web_app.py
```

**That's it!** 🎉 Your browser will open automatically to `http://localhost:8501`

![Web Interface Preview](https://via.placeholder.com/800x400/667eea/ffffff?text=Beautiful+Music+Dashboard)

## 🖥️ Hosting Options

### 🌟 Recommended: Streamlit Cloud (FREE!)

**Perfect for personal use** - Deploy your app in minutes:

1. **Fork this repo** on GitHub
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Connect your GitHub** and select this repo
4. **Set environment variables:**
   ```
   LASTFM_API_KEY=your_lastfm_key
   LASTFM_USERNAME=your_username
   OPENAI_API_KEY=your_openai_key (optional)
   ```
5. **Deploy!** ✨

**Result:** Your own hosted music recommendation system at `https://your-app.streamlit.app`

### 🚀 Professional Hosting Options

#### 1. **Railway** - `railway.app`
- **Cost:** $5/month
- **Perfect for:** Always-on personal apps
- **Features:** Custom domain, persistent storage
- **Deploy:** Connect GitHub, auto-deploys on push

#### 2. **Render** - `render.com`
- **Cost:** $7/month (free tier available)
- **Perfect for:** Reliable hosting with databases
- **Features:** Auto-scaling, SSL, monitoring

#### 3. **Google Cloud Run** - `cloud.google.com`
- **Cost:** Pay-per-use (very cheap for personal use)
- **Perfect for:** Serverless, scales to zero
- **Features:** Global CDN, automatic HTTPS

#### 4. **Digital Ocean App Platform**
- **Cost:** $5/month
- **Perfect for:** Simple deployment with databases
- **Features:** One-click deploy, managed databases

### 🏠 Home Server Options

#### **Docker Deployment**
```bash
# Clone repo
git clone [your-repo]
cd music-recommendation-system

# Build and run
docker build -t music-rec .
docker run -p 8501:8501 music-rec
```

#### **Raspberry Pi Setup**
Perfect for running at home 24/7:
```bash
# On your Pi
git clone [your-repo]
cd music-recommendation-system
pip install -r requirements.txt
python launch_web_app.py
```

Access from anywhere on your network at `http://pi-ip:8501`

### 📱 Mobile-Optimized Interface

The web app is fully responsive and works beautifully on:
- 📱 **iPhone/Android** - Touch-friendly controls
- 📟 **iPad/Tablet** - Perfect dashboard experience  
- 💻 **Desktop** - Full feature set with multiple columns
- 🖥️ **Large Screens** - Immersive data visualizations

## 🔧 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Last.fm API   │────│  Data Pipeline   │────│   Web Dashboard │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │  AI Recommender  │────│  Roon Integration│
                    └──────────────────┘    └─────────────────┘
```

## 📊 Feature Overview

### ✅ Phase 1: Data Collection (COMPLETE)
- Last.fm scrobble data fetching
- Automated data export and caching
- Comprehensive listening history analysis

### ✅ Phase 2: AI Analysis (COMPLETE)  
- OpenAI/Anthropic integration for music analysis
- Listening pattern recognition
- Personalized insights generation

### ✅ Phase 3: Metadata Enrichment (COMPLETE)
- MusicBrainz metadata integration
- Mood and genre classification
- Audio feature analysis

### ✅ Phase 4: Smart Recommendations (COMPLETE)
- AI-powered recommendation engine
- Context-aware playlist generation
- Multiple recommendation presets

### ✅ Phase 5: Roon Integration (COMPLETE)
- Real-time Roon Core connectivity
- Zone-specific playlist creation
- Automatic playlist synchronization
- Context-aware recommendations

### 🆕 Phase 6: Web Interface (NEW!)
- **Beautiful Streamlit dashboard**
- **Interactive visualizations**
- **Mobile-responsive design**
- **One-click hosting options**

## 🎯 CLI Commands (Still Available!)

For power users who love the terminal:

### Data Management
```bash
python -m src.music_rec.cli fetch --username your_username
python -m src.music_rec.cli export --username your_username
python -m src.music_rec.cli enrich --username your_username
python -m src.music_rec.cli analyze --username your_username
```

### Recommendations
```bash
python -m src.music_rec.cli recommend --username your_username --mood happy --energy high
python -m src.music_rec.cli preset --username your_username --preset discovery
```

### Roon Integration
```bash
python -m src.music_rec.cli roon-connect --core-host 192.168.1.100
python -m src.music_rec.cli roon-zones --core-host 192.168.1.100
python -m src.music_rec.cli roon-playlist --core-host 192.168.1.100 --zone-id kitchen
python -m src.music_rec.cli roon-sync --core-host 192.168.1.100
```

## 🔑 Environment Setup

Create a `.env` file:
```bash
# Last.fm API (Required)
LASTFM_API_KEY=your_lastfm_api_key
LASTFM_USERNAME=your_username

# AI Analysis (Optional but recommended)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Roon Integration (Optional)
ROON_CORE_HOST=192.168.1.100
ROON_APP_ID=music-recommendation-system
```

## 🛠️ Installation

### Option 1: Web Interface (Recommended)
```bash
git clone <repository-url>
cd music-recommendation-system
pip install -r requirements.txt
python launch_web_app.py
```

### Option 2: CLI Only
```bash
git clone <repository-url>
cd music-recommendation-system
pip install -r requirements.txt
python run.py
```

## 📈 What's Next?

- **🎵 Spotify Integration** - Direct playlist export to Spotify
- **🤖 Advanced AI Models** - Even smarter recommendations
- **👥 Social Features** - Share playlists with friends
- **🎨 Custom Themes** - Personalize your dashboard
- **📊 Advanced Analytics** - Deeper music insights

## 🤝 Contributing

We love contributions! Whether it's:
- 🐛 **Bug fixes**
- ✨ **New features** 
- 📚 **Documentation improvements**
- 🎨 **UI/UX enhancements**

## 📜 License

MIT License - see LICENSE file for details.

---

**🎵 Transform your music discovery journey with AI-powered recommendations and a beautiful, modern interface!** 