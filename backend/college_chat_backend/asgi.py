"""
ASGI config for college_chat_backend project.
Handles both HTTP (Django) and WebSocket (Channels) connections.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import chatbot.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chatbot.routing.websocket_urlpatterns
        )
    ),
})
