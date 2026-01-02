#!/bin/bash
# VLM Server Setup Script for macOS/Linux
# Installs and configures Ollama with SmolVLM model

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  VLM Server Setup (macOS/Linux)                ║"
echo "║                  Ollama + SmolVLM Installation                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo -e "\n✓ Detected OS: $OS"

# Step 1: Check if Ollama is installed
echo -e "\n[1/4] Checking Ollama installation..."

if command -v ollama &> /dev/null; then
    echo "✅ Ollama is already installed"
    ollama_version=$(ollama --version)
    echo "   Version: $ollama_version"
else
    echo "❌ Ollama is not installed"
    
    if [[ "$OS" == "macOS" ]]; then
        echo -e "\n📥 Installing Ollama (macOS)..."
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo "   Please install Homebrew first: https://brew.sh"
            echo "   Then run: brew install ollama"
            exit 1
        fi
    else
        echo -e "\n📥 Installing Ollama (Linux)..."
        curl https://ollama.ai/install.sh | sh
    fi
fi

# Step 2: Check if Ollama service is running
echo -e "\n[2/4] Checking Ollama service..."

if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama service is running"
else
    echo "⚠️  Ollama is not running. Starting..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 5
    
    if kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "✅ Ollama started (PID: $OLLAMA_PID)"
    else
        echo "❌ Failed to start Ollama"
        exit 1
    fi
fi

# Step 3: Pull SmolVLM model
echo -e "\n[3/4] Pulling SmolVLM model..."
echo "This may take a few minutes (model size: ~500MB)"

ollama pull smolvlm

if [ $? -eq 0 ]; then
    echo "✅ SmolVLM model installed successfully"
else
    echo "⚠️  Model pull might have failed. Checking..."
fi

# Step 4: Verify installation
echo -e "\n[4/4] Verifying installation..."

models=$(ollama list)
if echo "$models" | grep -q "smolvlm"; then
    echo "✅ SmolVLM is available"
else
    echo "⚠️  SmolVLM not found in available models"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       SETUP COMPLETE                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo -e "\n📋 Next Steps:"
echo "  1. Start Ollama server (if not running):"
echo "     ollama serve"
echo ""
echo "  2. In another terminal, run the backend:"
echo "     cd backend"
echo "     python main.py"
echo ""
echo "  3. Test VLM integration:"
echo "     python test_vlm.py"
echo ""
echo "  4. Try the API endpoint:"
echo "     curl -X POST http://localhost:8000/api/ask_context \\"
echo "       -F 'image=@scene.jpg' \\"
echo "       -F 'question=Önümde ne var?'"

echo -e "\n📚 Resources:"
echo "  - Setup guide: docs/VLM_SETUP.md"
echo "  - Ollama: https://ollama.ai"
echo "  - SmolVLM: https://huggingface.co/xtuner/SmolVLM-256M"
