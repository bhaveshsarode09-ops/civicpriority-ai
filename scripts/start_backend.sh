#!/bin/bash
# Start CivicPriority FastAPI Backend on port 5050
export PYTHONPATH=backend/src
exec python3 -m uvicorn --app-dir backend/src civicpriority.api:app --host 127.0.0.1 --port 5050
