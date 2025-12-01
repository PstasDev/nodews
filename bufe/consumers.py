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
            elif message_type == 'add_product':
                # Handle add product request
                await self.handle_add_product(data)
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
    
    async def product_update(self, event):
        """
        Handle product update events from the group.
        Send the product data to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'product_update',
            'action': event['action'],
            'product': event['product']
        }))
    
    async def handle_add_product(self, data):
        """
        Handle add product request via WebSocket.
        """
        try:
            # Extract product data
            product_data = {
                'nev': data.get('nev', ''),
                'kategoria_id': data.get('kategoria_id'),
                'ar': data.get('ar', 0),
                'max_rendelesenkent': data.get('max_rendelesenkent', 1),
                'hutve': data.get('hutve', False),
                'elerheto': data.get('elerheto', True),
                'kisult': data.get('kisult', False)
            }
            
            # Validate required fields
            if not product_data['nev'] or not product_data['kategoria_id']:
                await self.send(text_data=json.dumps({
                    'type': 'add_product_response',
                    'success': False,
                    'error': 'Hiányzó kötelező mezők (név, kategória)'
                }))
                return
            
            # Create product
            product = await self.create_product(product_data)
            
            if product:
                # Send success response
                await self.send(text_data=json.dumps({
                    'type': 'add_product_response',
                    'success': True,
                    'product': {
                        'id': product.id,
                        'nev': product.nev,
                        'kategoria_id': product.kategoria.id,
                        'kategoria_nev': product.kategoria.nev,
                        'ar': product.ar,
                        'max_rendelesenkent': product.max_rendelesenkent,
                        'hutve': product.hutve,
                        'elerheto': product.elerheto,
                        'kisult': product.kisult
                    }
                }))
                
                # Broadcast to all admin clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'product_update',
                        'action': 'add',
                        'product': {
                            'id': product.id,
                            'nev': product.nev,
                            'kategoria_id': product.kategoria.id,
                            'kategoria_nev': product.kategoria.nev,
                            'ar': product.ar,
                            'max_rendelesenkent': product.max_rendelesenkent,
                            'hutve': product.hutve,
                            'elerheto': product.elerheto,
                            'kisult': product.kisult
                        }
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    'type': 'add_product_response',
                    'success': False,
                    'error': 'Hiba a termék létrehozásában'
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'add_product_response',
                'success': False,
                'error': str(e)
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
    
    @database_sync_to_async
    def create_product(self, product_data):
        """
        Create a new product in the database.
        """
        try:
            from .models import Termek, Kategoria
            
            kategoria = Kategoria.objects.get(id=product_data['kategoria_id'])
            
            termek = Termek.objects.create(
                nev=product_data['nev'],
                kategoria=kategoria,
                ar=int(product_data['ar']),
                max_rendelesenkent=int(product_data['max_rendelesenkent']),
                hutve=bool(product_data['hutve']),
                elerheto=bool(product_data['elerheto']),
                kisult=bool(product_data['kisult'])
            )
            
            return termek
        except Exception as e:
            print(f"Error creating product: {e}")
            return None
