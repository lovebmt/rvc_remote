# myboard/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/myboard/(?P<room_name>\w+)/$', consumers.messageClientConsumer.as_asgi()),
]