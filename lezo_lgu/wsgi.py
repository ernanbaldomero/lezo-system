"""
WSGI config for Lezo LGU System project.
Optimized for single-worker Gunicorn deployment.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lezo_lgu.settings')

application = get_wsgi_application()