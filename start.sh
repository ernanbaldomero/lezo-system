#!/bin/bash
# Startup script for Lezo LGU System
source venv/bin/activate
gunicorn -b 0.0.0.0:8000 --workers 1 lezo_lgu.wsgi
