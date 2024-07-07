from rest_framework import serializers
from core_post.models import Save
from django.contrib.auth import get_user_model
from core_post.serializers import UserPostSerializer
from core_profile.models import Story, StoryVideos, StoryPics
from core_account.models import interest
User = get_user_model()



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    class Meta:
        model = User
        fields = ['profile', 'profile_slug', 'profile_info', 'username', 'email', 'date_of_birth']


class GetProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving user profiles.
    """
    post = UserPostSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['id', 'profile', 'profile_slug', 'profile_info', 'full_name', 'username', 'date_of_birth', 'post']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profiles.
    """
    Interest = serializers.PrimaryKeyRelatedField(many=True, queryset=interest.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'date_of_birth', 'mobile_number', 'profile', 'profile_info', 'Interest']
        extra_kwargs = {
            'email': {'required': False},
            'full_name': {'required': False},
            'date_of_birth': {'required': False},
            'mobile_number': {'required': False},
            'profile': {'required': False},
            'profile_info': {'required': False},
        }

class UserdSerializer(serializers.Serializer):
    """
    Serializer for user identification.
    """
    user_id = serializers.IntegerField()


class SaveSerializer(serializers.ModelSerializer):
    """
    Serializer for the Save model.
    """
    post = UserPostSerializer(read_only=True)  # Remove many=True here

    class Meta:
        model = Save
        fields = ['user', 'post', 'date_time']


class VideosSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryVideos
        fields = "__all__"

class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryPics
        fields = "__all__"

class StorySerializer(serializers.ModelSerializer):
    images = ImagesSerializer(many=True)
    videos = VideosSerializer(many=True)

    class Meta:
        model = Story
        fields = "__all__"