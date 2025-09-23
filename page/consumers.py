import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Conversation
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from channels.db import database_sync_to_async
from .bot_service import get_bot_response


# --- Chat Consumer ---
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        params = dict(p.split('=') for p in query_string.split('&'))
        token_key = params.get('token')

        if not token_key:
            await self.close();
            return

        try:
            access_token = AccessToken(token_key)
            self.user = await self.get_user_from_token(access_token)
        except (InvalidToken, User.DoesNotExist):
            await self.close();
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'

        is_participant = await self.is_user_participant()
        if self.user and self.user.is_authenticated and is_participant:
            await self.channel_layer.group_add(self.conversation_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.conversation_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json['message']
        await self.save_message(message_text)
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {'type': 'chat_message', 'message': message_text, 'sender': self.user.username}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message'], 'sender': event['sender']}))

    @database_sync_to_async
    def get_user_from_token(self, access_token):
        return User.objects.get(id=access_token['user_id'])

    @database_sync_to_async
    def is_user_participant(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_text):
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(conversation=conversation, sender=self.user, text=message_text)


# --- Chatbot Consumer ---
class BotChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        bot_response = await sync_to_async(get_bot_response)(message)

        await self.send(text_data=json.dumps({
            'sender': 'SkillBot',
            'message': bot_response
        }))
