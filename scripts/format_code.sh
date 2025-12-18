#!/bin/bash
# Auto-format all Python code with Black

echo "🎨 Formatting Python code with Black..."

cd backend

if ! command -v black &> /dev/null; then
    echo "Installing black..."
    pip install black
fi

black .

echo "✅ Code formatted!"
