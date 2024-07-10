# asgi.py

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'processor.settings')
import django
# Ensure Django is initialized correctly
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from processor.middleware import JwtAuthForAsgi



from core_messaging.routing import websocket_urlpatterns  # Ensure this import is correct

# Application instance definition
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        JwtAuthForAsgi(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
