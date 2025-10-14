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

# Wrap Django ASGI app with WhiteNoise for static file serving
from whitenoise import WhiteNoise
from django.conf import settings

# Apply WhiteNoise to Django ASGI app for static files
static_app = WhiteNoise(django_asgi_app, root=settings.STATIC_ROOT, prefix=settings.STATIC_URL)
# Add additional static file directories
for directory in settings.STATICFILES_DIRS:
    static_app.add_files(str(directory), prefix=settings.STATIC_URL)

application = ProtocolTypeRouter({
    "http": static_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
