#!/bin/bash

# Fire Spread Simulation Web Application - Start Script

echo "🔥 Fire Spread Simulation Web Application"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# # Create virtual environment if it doesn't exist
# if [ ! -d "venv" ]; then
#     echo "📦 Creating virtual environment..."
#     python3 -m venv venv
# fi

# # Activate virtual environment
# echo "🔄 Activating virtual environment..."
# source venv/bin/activate

# # Install dependencies
# echo "📥 Installing dependencies..."
# $PIP_CMD install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p temp data static/images

# Check if Chrome/Chromium is installed
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome found"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium browser found"
elif command -v chromium &> /dev/null; then
    echo "✅ Chromium found"
else
    echo "⚠️  Chrome/Chromium not found. Some terrain extraction features may not work."
    echo "   Install Chrome or Chromium for full functionality."
fi

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start the application
echo "🚀 Starting Fire Spread Simulation Web Application..."
echo "🌐 Open your browser and navigate to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

python app.py
