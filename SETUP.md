# Setup Instructions

## Create Virtual Environment

### Option 1: Using `venv` (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Option 2: Using `virtualenv`

```bash
# Install virtualenv if not already installed
pip install virtualenv

# Create virtual environment
virtualenv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

## Install Dependencies

```bash
# Make sure virtual environment is activated (you should see (venv) in your prompt)
pip install -r requirements.txt
```

## Verify Installation

```bash
# Check Python version (should be 3.8+)
python --version

# Check installed packages
pip list

# Test import
python -c "import langchain_ollama; print('✅ Dependencies installed')"
```

## Deactivate Virtual Environment

```bash
deactivate
```

## Quick Setup Script

Run this to set everything up:

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify
python -c "import langchain_ollama; print('✅ Setup complete!')"
```

## Troubleshooting

### If `python3` command not found:
- Try `python` instead
- Or install Python 3.8+ from python.org

### If `venv` module not found:
- Install Python 3.8+ which includes venv
- Or use `virtualenv` instead

### If import errors after installation:
- Make sure virtual environment is activated
- Reinstall: `pip install -r requirements.txt --force-reinstall`

