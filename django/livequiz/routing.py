from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/live/play/(?P<live_quiz_id>\w+)$',
            consumers.LiveQuizConsumer.as_asgi()),
]
