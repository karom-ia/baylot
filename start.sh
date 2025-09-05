#!/bin/bash
export ENVIRONMENT=production
export HOST=0.0.0.0
export PORT=8000

# Запускаем сервер с логированием
uvicorn main:app --host $HOST --port $PORT --log-level info