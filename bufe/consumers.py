"""
WebSocket consumers for real-time order notifications.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Bufe, Rendeles


class OrderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting order updates to bufeadmin users.
    """
    
    async def connect(self):
        """
        Handle WebSocket connection.
        Only allow authenticated bufeadmin users to connect.
        """
        self.user = self.scope["user"]
        
        # Check if user is authenticated and is a bufeadmin
        if not await self.is_bufeadmin():
            await self.close()
            return
        
        # Join the orders broadcast group
        self.room_group_name = 'bufe_orders'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        # Leave the orders broadcast group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def order_update(self, event):
        """
        Handle order update events from the group.
        Send the order data to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'action': event['action'],
            'order': event['order']
        }))
    
    @database_sync_to_async
    def is_bufeadmin(self):
        """
        Check if the current user is a bufeadmin.
        """
        if not self.user.is_authenticated:
            return False
        
        try:
            bufe = Bufe.objects.first()
            if not bufe:
                return False
            
            return bufe.bufeadmin.filter(id=self.user.id).exists()
        except Exception:
            return False
