#!/bin/bash
# Startup script for Lezo LGU System
# Optimized for lightweight operation

source venv/bin/activate
gunicorn -b 0.0.0.0:8000 --workers 1 lezo_lgu.wsgi  # Single worker for 1GB RAM