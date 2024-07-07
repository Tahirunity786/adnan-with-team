from django.db import models
from core_account.manager import CustomUserManager
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.utils.text import slugify
import uuid

class interest(models.Model):
    interests = models.CharField(max_length=200, default="", db_index=True)

class User(AbstractUser):
    """
    Custom User model inheriting from Django's AbstractUser.

    Attributes:
        GENDER (tuple): Choices for the gender field.
    """

    GENDER = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Not confirmed", "Not confirmed"),
    )

    MODE = (
        ("Public", "Public"),
        ("Private", "Private"),
    )

    TWOFAUTH = (
        ("Email", "Email"),
        ("SMS", "SMS"),
        ("Whatsapp SMS", "Whatsapp SMS"),
    )

    # General Information about the user
    profile = models.ImageField(upload_to="profile/images", blank=True, null=True)  # User's profile picture
    profile_slug = models.SlugField(unique=True, default='')  # Slug field for user's profile
    profile_info = models.CharField(max_length=100, null=True, blank=True)  # Additional profile information
    full_name = models.CharField(max_length=100)  # User's full name
    username = models.CharField(max_length=100, unique=True, db_index=True)  # User's username
    email = models.EmailField(null=False, unique=True)  # User's email address
    date_of_birth = models.DateField(default=None, null=True)  # User's date of birth
    gender = models.CharField(max_length=100, choices=GENDER, null=True, db_index=True)  # User's gender
    Interest = models.ManyToManyField(interest, blank=True)
    mobile_number = models.BigIntegerField(null=True)  # User's mobile number
    otp = models.PositiveIntegerField(null=True)  # One-time password for verification
    otp_limit = models.IntegerField(null=True)  # Limit for OTP attempts
    otp_delay = models.TimeField(auto_now=True)  # Delay between OTP attempts
    date_joined = models.DateTimeField(auto_now_add=True)  # Date and time when user joined
    last_login = models.DateTimeField(default=None, null=True)  # Date and time of last login
    is_blocked = models.BooleanField(default=False, null=True)  # Flag indicating if user is blocked
    is_verified = models.BooleanField(default=False)  # Flag indicating if user is verified
    # Account mode Public/Private
    account_mode = models.CharField(max_length=100, choices=MODE, default="Public", db_index=True)
    # Boolean for two factor authentication
    two_factor_auth = models.BooleanField(default = False)
    two_factor_auth_method = models.CharField(max_length=100, choices=TWOFAUTH,null=True, db_index=True)
    # Fields provided
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)  # Users who follow this user
    close_friends = models.ManyToManyField('self', blank=True)  # Users marked as close friends
    blockel_peoples = models.ManyToManyField('self', blank=True)  # Users marked as close friends
    mute_peoples = models.ManyToManyField('self', blank=True)  # Users marked as close friends


    password = models.CharField(max_length=200, db_index=True, default=None)  # Password field
    USERNAME_FIELD = 'email'  # Username used for authentication
    REQUIRED_FIELDS = ['username']  # Required fields for creating a user (excluding email)

    objects = CustomUserManager()  # Custom manager for the User model

    # Unique related_name for groups and user_permissions
    groups = models.ManyToManyField(Group, related_name='user_groups', blank=True)  # Groups associated with the user
    user_permissions = models.ManyToManyField(Permission, related_name='user_permissions', blank=True)  # Permissions assigned to the user

    def save(self, *args, **kwargs):
        """
        Custom save method to auto-generate profile_slug from username.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.profile_slug = slugify(self.username)
        self.profile_slug += f"-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

