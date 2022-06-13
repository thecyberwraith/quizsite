from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/live/(?P<live_game_id>\w+)/$', consumers.LiveQuizConsumer.as_asgi())
]