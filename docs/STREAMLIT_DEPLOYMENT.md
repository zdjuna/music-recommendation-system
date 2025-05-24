# 🚀 Streamlit Cloud Deployment Guide

Deploy your Music Recommendation System to Streamlit Cloud for free hosting with beautiful web interface.

## 🌟 Quick Deploy (2 minutes!)

### Step 1: Fork the Repository
1. Go to this repository on GitHub
2. Click **Fork** to create your own copy
3. Make sure the fork is public (required for free Streamlit Cloud)

### Step 2: Deploy to Streamlit Cloud
1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select:
   - **Repository:** your-username/music-recommendation-system
   - **Branch:** main
   - **Main file path:** streamlit_app.py
5. Click **Deploy!**

### Step 3: Configure Your API Keys
In the Streamlit Cloud interface:

1. Click **"⚙️ Settings"** → **"Secrets"**
2. Add your configuration:

```toml
# Required - Get from https://www.last.fm/api/account/create
LASTFM_API_KEY = "your_lastfm_api_key_here"
LASTFM_API_SECRET = "your_lastfm_api_secret_here"
LASTFM_USERNAME = "zdjuna"

# Professional Mood Analysis (Highly Recommended)
CYANITE_API_KEY = "your_cyanite_api_key_here"

# AI Analysis (Optional but recommended)
OPENAI_API_KEY = "your_openai_api_key_here"  # For GPT-4.1
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"  # For Claude 3.5 Sonnet

# Roon Integration (Optional)
ROON_CORE_HOST = "192.168.1.213"
ROON_CORE_PORT = "9100"

# Optional Services
MUSICBRAINZ_USER_AGENT = "MusicRecSystem/1.0 (your_email@example.com)"
QOBUZ_API_KEY = "your_qobuz_api_key_here"
QOBUZ_API_SECRET = "your_qobuz_api_secret_here"
TIDAL_API_KEY = "your_tidal_api_key_here"
```

3. Click **Save**

### Step 4: Launch! 🎉
Your app will be available at: `https://your-app-name.streamlit.app`

## 🔧 Advanced Configuration

### Custom Domain
1. In Streamlit Cloud settings
2. Go to **"General"** → **"App settings"**
3. Add your custom domain (requires DNS setup)

### Environment Variables vs Secrets
- **Secrets** (recommended): Encrypted, not visible in logs
- **Config variables**: Use for non-sensitive settings

### App Settings
```toml
# Performance tuning
MAX_TRACKS_PER_REQUEST = "200"
DEFAULT_DISCOVERY_LEVEL = "medium"
RATE_LIMIT_DELAY = "1.0"
LOG_LEVEL = "INFO"
```

## 🎵 Features Available on Streamlit Cloud

### ✅ Fully Functional
- **📊 Interactive Dashboard** - All visualizations work perfectly
- **🎯 Smart Recommendations** - AI-powered playlist generation
- **📱 Mobile Interface** - Responsive design on all devices
- **💾 Export Functions** - Download playlists as M3U/CSV/JSON
- **🎭 Cyanite.ai Integration** - Professional mood analysis

### ⚠️ Limited Features
- **🎵 Roon Integration** - Only works if Roon Core is publicly accessible
- **📥 Data Fetching** - May timeout for large datasets (use CLI for initial setup)

### 🚫 Not Available
- **File System Access** - Use cloud storage for large datasets
- **Background Jobs** - Streamlit apps sleep after inactivity

## 🔐 Security Best Practices

### API Key Management
- **Never commit API keys** to your repository
- **Use Streamlit Secrets** for all sensitive data
- **Rotate keys regularly** especially if shared

### Access Control
- **Keep repo public** for free Streamlit Cloud
- **Use environment-based access control** if needed
- **Monitor API usage** to detect unauthorized access

## 🐛 Troubleshooting

### Common Issues

#### "Module not found" Error
**Solution:** Add missing dependencies to `requirements.txt`

#### App Won't Start
**Solutions:**
1. Check `requirements.txt` for correct package versions
2. Verify `streamlit_app.py` is in repository root
3. Check Streamlit Cloud logs for detailed error messages

#### Missing API Keys
**Solutions:**
1. Verify secrets are correctly formatted in Streamlit Cloud
2. Check for typos in secret names
3. Ensure quotes around string values in TOML format

#### Slow Performance
**Solutions:**
1. Reduce `MAX_TRACKS_PER_REQUEST` in secrets
2. Cache frequently used data
3. Consider upgrading to Streamlit Cloud Pro

### Getting Help
- **Streamlit Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io)
- **Streamlit Documentation:** [docs.streamlit.io](https://docs.streamlit.io)
- **GitHub Issues:** Use this repository's issue tracker

## 🎯 Next Steps

After successful deployment:

1. **📊 Import Your Data**
   - Run CLI commands locally first for large datasets
   - Upload processed data to cloud storage if needed

2. **🎵 Set Up Integrations**
   - Configure Cyanite.ai for professional mood analysis
   - Add AI analysis with OpenAI or Anthropic
   - Connect Roon if accessible from internet

3. **🎨 Customize**
   - Modify themes and styling in `streamlit_app.py`
   - Add custom visualization types
   - Extend with additional music services

4. **📱 Share**
   - Share your app URL with friends
   - Add to your music setup documentation
   - Consider creating tutorial videos

## 🌟 Pro Tips

### Performance Optimization
- **Cache data** using `@st.cache_data` decorator
- **Minimize API calls** by caching responses
- **Use session state** for user preferences

### User Experience
- **Add loading spinners** for long operations
- **Include help text** for complex features
- **Test on mobile devices** regularly

### Monitoring
- **Check Streamlit Cloud analytics** for usage patterns
- **Monitor API quotas** to avoid service interruption
- **Set up alerts** for app downtime

---

🎵 **Enjoy your personal music recommendation system in the cloud!** 🎉 