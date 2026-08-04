#!/usr/bin/env bash
echo "==================================================="
echo "  J.A.R.V.I.S. Mark XLI -- Automated Setup Engine"
echo "==================================================="
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Detect Python 3
PYCMD=""
if command -v python3 &>/dev/null; then
    PYCMD="python3"
elif command -v python &>/dev/null; then
    PYCMD="python"
else
    echo "[ERROR] Python 3 is not installed."
    echo "Please install Python 3.10+ and try again."
    exit 1
fi

echo "[1/3] Using Python: $($PYCMD --version)"

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "[2/3] Creating virtual environment (venv)..."
    $PYCMD -m venv venv || { echo "[ERROR] Could not create venv."; exit 1; }
fi

# Install dependencies inside venv
echo "[3/3] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create config/api_keys.json template if missing
if [ ! -f "config/api_keys.json" ]; then
    if [ -f "config/api_keys.json.example" ]; then
        cp config/api_keys.json.example config/api_keys.json
        echo "Created config/api_keys.json from template."
    else
        echo '{"gemini_api_key": ""}' > config/api_keys.json
    fi
fi

echo ""
echo "==================================================="
echo "  SETUP COMPLETE!"
echo "==================================================="
echo "Next Steps:"
echo "1. Add your Gemini API Key in config/api_keys.json"
echo "2. Launch JARVIS with: ./main.sh"
echo ""
