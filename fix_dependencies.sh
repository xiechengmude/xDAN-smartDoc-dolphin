#!/bin/bash

echo "🔧 Fixing aioredis dependency for Python 3.11 compatibility..."
echo "=================================================="

# Uninstall incompatible aioredis version
echo "📦 Uninstalling aioredis 2.0.1 (incompatible with Python 3.11)..."
pip uninstall aioredis -y

# Install compatible aioredis version
echo "📦 Installing aioredis 2.0.6+ (Python 3.11 compatible)..."
pip install "aioredis>=2.0.6"

# Install or update other dependencies
echo "📦 Installing/updating other required dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies fixed! You can now run the server:"
echo "   python start_xdan_vision_server.py --port 8001" 