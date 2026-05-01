#!/bin/bash

export DISPLAY=:0

cd /home/minijarvis/minijarvis

# Activate environment
source venv/bin/activate

# Wait for system to stabilize
sleep 10

# Warm up model
OLLAMA_KEEP_ALIVE=24h ollama run qwen2.5:3b-instruct-q8_0 "Hello" > /dev/null 2>&1

# Launch UI
python3 jarvis_ui.py
