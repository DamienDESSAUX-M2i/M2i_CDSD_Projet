#!/usr/bin/env sh

set -e

echo "Starting FastAPI..."

uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 &

echo "Starting Streamlit..."

exec streamlit run frontend/streamlit_app.py \
    --server.address=0.0.0.0 \
    --server.port=7860 \
    --server.headless=true