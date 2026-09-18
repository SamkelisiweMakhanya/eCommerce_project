"""
WSGI config for the project project.

This module configures the WSGI application used to serve the Django
project with WSGI-compatible web servers.

It exposes the WSGI callable as a module-level variable named
``application``.

For more information on this file, see:
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the WSGI application.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")


# Create the WSGI application callable for the Django project.
application = get_wsgi_application()