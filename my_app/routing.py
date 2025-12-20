from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/test/(?P<block_id>\w+)/$', consumers.TestConsumer.as_asgi()),
]
