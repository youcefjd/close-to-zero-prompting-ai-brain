#!/bin/bash

# Quick setup script for virtual environment

echo "🔧 Setting up virtual environment..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "✅ Virtual environment created"
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Verify installation
echo ""
echo "✅ Setup complete!"
echo ""
echo "Virtual environment is now active (you should see (venv) in your prompt)"
echo ""
echo "To activate manually in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
echo "Testing imports..."
python -c "import langchain_ollama; print('✅ All dependencies installed successfully!')" 2>/dev/null || echo "⚠️  Some dependencies may need manual installation"

