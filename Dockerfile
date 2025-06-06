# 🎵 Music Recommendation System - Docker Image
FROM python:3.11-slim

LABEL maintainer="Music Recommendation System"
LABEL description="Beautiful AI-powered music recommendation web app"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p data config playlists reports logs backups \
    && chmod 755 data config playlists reports logs backups

# Make scripts executable
RUN chmod +x *.py

# Create non-root user for security
RUN useradd -m -u 1000 musicrec && \
    chown -R musicrec:musicrec /app
USER musicrec

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check using our custom health check script
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python health_check.py > /dev/null 2>&1 || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]