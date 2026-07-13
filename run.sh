#!/bin/bash
# run.sh - Render/Linux deployment script
# Boots both FastAPI (backend) and Streamlit (frontend) on a single instance

# Start FastAPI backend in the background on an internal port
echo "Starting FastAPI backend..."
uvicorn api.server:app --host 0.0.0.0 --port 8000 &

echo "Waiting 5 seconds for backend to initialize..."
sleep 5

# Start Streamlit frontend in the foreground on the public PORT exposed by Render
echo "Starting Streamlit frontend..."
streamlit run main.py --server.port ${PORT:-8501} --server.address 0.0.0.0
