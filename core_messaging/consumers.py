import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncConsumer
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import ChatThread, Chatmessage
from .serializers import ChatMessageSerializer
from .validator import validate_file_type, validate_file_size, scan_file_for_viruses
import logging
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.db.models import Q

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        second_user = self.scope['target']
        first_user = self.scope['user']
        thread = await self.get_thread(first_user, second_user)
        self.chatroom = f'chatroom_{thread.id}'
        self.thread = thread

        await self.channel_layer.group_add(
            self.chatroom,
            self.channel_name
        )
        await self.send({"type": "websocket.accept"})

        # Notify the secondary user about the new thread
        await self.notify_secondary_user(thread, second_user)

        # Fetch chat history
        chat_history = await self.fetch_chat_history(thread)
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "type": "chat_history",
                "messages": chat_history
            })
        })

    async def websocket_receive(self, event):
        try:
            message_data = json.loads(event['text'])
            logger.info(f"Received message data: {message_data}")

            message = message_data.get('message')
            image = message_data.get('image')
            file = message_data.get('file')

            if not message and not image and not file:
                raise ValueError("No message content or file provided")

            if not self.scope['user'] or not self.scope['target'] or not self.thread:
                raise ValueError("Invalid user, target, or thread")

            # Ensure user and thread are valid
            user = await self.get_user(self.scope['user'].id)
            thread = await self.get_thread(self.scope['user'], self.scope['target'])
            if not user or not thread:
                raise ValueError("User or thread not found")

            # Validate and scan files
            if image:
                await self.validate_and_scan_file(image)
            if file:
                await self.validate_and_scan_file(file)

            # Save the message
            msg = await self.save_message(thread, user, message, image, file)
            data = ChatMessageSerializer(msg, many=False).data

            response = {
                'message': json.dumps(data),
            }

            await self.channel_layer.group_send(
                self.chatroom,
                {
                    'type': 'chat_message',
                    'text': json.dumps(response)
                }
            )

            # Update the last message time for the primary user
            if user.id == self.scope['user'].id:
                await self.update_last_message_time(thread)
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({'error': 'Invalid JSON data received'})
            })
        except ValidationError as e:
            logger.error(f"ValidationError: {e}")
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({'error': str(e)})
            })
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({'error': str(e)})
            })
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({'error': 'Internal server error'})
            })

    async def chat_message(self, event):
        await self.send({'type': 'websocket.send', 'text': event['text']})

    async def websocket_disconnect(self, event):
        await self.check_messages_count(self.thread)
        await self.channel_layer.group_discard(
            self.chatroom,
            self.channel_name
        )

    @database_sync_to_async
    def get_user(self, user_id):
        usr = User.objects.filter(id=user_id)
        if usr.exists():
            return usr.first()
        return None

    @database_sync_to_async
    def check_messages_count(self, thread):
        if thread.chatmessage_thread.all().count() == 0:
            thread.delete()

    @database_sync_to_async
    def get_thread(self, first_person, second_person):
        thread = ChatThread.objects.filter(
            Q(primary_user=first_person, secondary_user=second_person) |
            Q(primary_user=second_person, secondary_user=first_person)
        ).first()

        if thread:
            return thread
        return ChatThread.objects.create(primary_user=first_person, secondary_user=second_person)

    @database_sync_to_async
    def save_message(self, thread, user, message, image=None, file=None):
        return Chatmessage.objects.create(thread=thread, user=user, message=message, image=image, file=file)

    @database_sync_to_async
    def fetch_chat_history(self, thread):
        messages = Chatmessage.objects.filter(thread=thread).order_by('message_time')
        return ChatMessageSerializer(messages, many=True).data

    @database_sync_to_async
    def update_last_message_time(self, thread):
        thread.primary_last_message_time = timezone.now()
        thread.save()

    @database_sync_to_async
    def notify_secondary_user(self, thread, second_user):
        # Notify the secondary user about the new thread
        # Assuming you have a method to send a WebSocket message to the secondary user
        # Example:
        async_to_sync(self.channel_layer.group_send)(
            f'user_{second_user.id}',
            {
                'type': 'new_thread_notification',
                'thread_id': thread.id
            }
        )

    async def validate_and_scan_file(self, file):
        validate_file_type(file)
        validate_file_size(file)
        scan_file_for_viruses(file)

    async def new_thread_notification(self, event):
        # Handle the notification of a new thread
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "type": "new_thread",
                "thread_id": event['thread_id']
            })
        })