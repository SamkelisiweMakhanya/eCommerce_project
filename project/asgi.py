"""
ASGI config for the project project.

This module configures the ASGI application used to serve the Django
project with ASGI-compatible web servers.

It exposes the ASGI callable as a module-level variable named
``application``.

For more information on this file, see:
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set the default Django settings module for the ASGI application.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")


# Create the ASGI application callable for the Django project.
application = get_asgi_application()
