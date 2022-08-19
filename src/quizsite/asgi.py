"""
ASGI config for getasgi project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

from django.core.asgi import get_asgi_application
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizsite.settings')
http_application = get_asgi_application()


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import livequiz.routing

application = ProtocolTypeRouter({
    'http': http_application,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            livequiz.routing.websocket_urlpatterns
        )
    ),
})
