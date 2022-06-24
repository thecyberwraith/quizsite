from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/live/host/(?P<quiz_code>\w+)$',
            consumers.LiveQuizHostConsumer.as_asgi()),
    re_path(r'ws/live/play/(?P<quiz_code>\w+)$',
            consumers.LiveQuizParticipantConsumer.as_asgi())
]
