"""
ASGI config for nodews_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nodews_project.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import these after get_asgi_application() to ensure apps are loaded
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from bufe.routing import websocket_urlpatterns

# For ASGI applications with Daphne, Django's staticfiles handler works with WhiteNoise middleware
# The WhiteNoise middleware in settings.py handles static files for HTTP requests
# No need to wrap the ASGI app directly - WhiteNoise middleware does it automatically

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
