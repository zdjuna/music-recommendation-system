#!/bin/bash

echo "🎵 Music Recommendation System Setup"
echo "===================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully!"
    else
        echo "❌ Failed to create virtual environment."
        exit 1
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi

# Create config file if it doesn't exist
if [ ! -f "config/config.env" ]; then
    echo
    echo "📝 Setting up configuration..."
    
    if [ -f "config/config_template.env" ]; then
        cp config/config_template.env config/config.env
        echo "✅ Created config/config.env from template"
        echo
        echo "🔑 Next steps:"
        echo "1. Get your Last.fm API key from: https://www.last.fm/api/account/create"
        echo "2. Edit config/config.env with your API credentials"
        echo "3. Run: source venv/bin/activate && python3 run.py"
    else
        echo "❌ Template file not found. Something went wrong with the setup."
        exit 1
    fi
else
    echo "✅ Configuration file already exists"
fi

echo
echo "🎉 Setup complete!"
echo
echo "To get started:"
echo "1. Edit config/config.env with your Last.fm API credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python3 run.py"
echo "4. Choose option 2 to test your API connection"
echo "5. Choose option 3 to fetch your music data"
echo
echo "💡 Remember to activate the virtual environment each time:"
echo "   source venv/bin/activate"
echo
echo "Happy listening! 🎧" 