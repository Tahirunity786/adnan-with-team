from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from core_account.utiles import generate_otp
from core_account.models import interest
User = get_user_model()

class CreateUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    Interest = serializers.PrimaryKeyRelatedField(many=True, queryset=interest.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'password', 'password2', 'Interest']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        password = data.get('password')
        password2 = data.pop('password2', None)

        validate_password(password)

        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords do not match'})

        return data

    def create(self, validated_data):
        email = validated_data.pop('email', None)
        if email is None:
            raise serializers.ValidationError({'email': 'Email field is required'})

        validated_data['username'] = validated_data.get('username')
        validated_data['password'] = validated_data.get('password')

        user = User.objects.create_user(email=email, **validated_data)
        user.account_mode = "Public"

        return user


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token and provider.
    """
    provider = serializers.CharField(max_length=255, required=True)
    access_token = serializers.CharField(max_length=4096, required=True, trim_whitespace=True)



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'date_of_birth', 'mobile_number', 'profile']

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting password.
    """
    new_password = serializers.CharField(max_length=128, min_length=8)
    confirm_new_password = serializers.CharField(max_length=128, min_length=8)

    def validate(self, data):
        if data.get('new_password') != data.get('confirm_new_password'):
            raise serializers.ValidationError("The new passwords do not match.")
        return data