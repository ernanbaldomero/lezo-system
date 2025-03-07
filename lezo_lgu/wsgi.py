"""
WSGI config for Lezo LGU System project.

This module contains the WSGI application used by Gunicorn to serve the Django project.
It exposes the WSGI callable as a module-level variable named ``application``.

For more information on WSGI, see:
- https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
- https://www.python.org/dev/peps/pep-3333/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the 'lezo_lgu' project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lezo_lgu.settings')

# Create the WSGI application callable
application = get_wsgi_application()
