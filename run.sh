#!/bin/bash

echo "🚀 Starting Swayami Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your settings before running the server."
    echo "Required: MONGODB_URI, OPENAI_API_KEY"
    exit 1
fi

# Start the server
echo "🌟 Starting FastAPI server..."
python main.py 