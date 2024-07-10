from rest_framework import serializers
from core_messaging.models import Chatmessage
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name', 'last_name','profile')


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chatmessage
        fields = ['id', 'thread', 'user', 'message', 'message_time', 'image', 'file']