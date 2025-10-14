"""
WebSocket URL routing for bufe app.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/bufe/orders/$', consumers.OrderConsumer.as_asgi()),
]
