import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import TestBlock

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.block_id = self.scope['url_route']['kwargs']['block_id']
        self.room_group_name = f'test_{self.block_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send initial time info
        block_info = await self.get_block_info()
        await self.send(text_data=json.dumps({
            'type': 'init',
            'data': block_info
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'timer_update':
            # Broadcast timer to all users in this test
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'timer_message',
                    'elapsed': data.get('elapsed')
                }
            )

    async def timer_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'timer',
            'elapsed': event['elapsed']
        }))

    @database_sync_to_async
    def get_block_info(self):
        try:
            block = TestBlock.objects.get(id=self.block_id)
            return {
                'savol_vaqti': block.savol_vaqti,
                'vaqt_turi': block.vaqt_turi,
                'boshlash_vaqti': block.boshlash_vaqti.isoformat() if block.boshlash_vaqti else None,
                'tugash_vaqti': block.tugash_vaqti.isoformat() if block.tugash_vaqti else None,
            }
        except TestBlock.DoesNotExist:
            return {}
