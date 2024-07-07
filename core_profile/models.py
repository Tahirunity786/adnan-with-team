from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.

class StoryVideos(models.Model):
    video = models.FileField(upload_to="usr/story/video", null=True, blank=True)

class StoryPics(models.Model):
    image = models.ImageField(upload_to="usr/story/pic", null=True, blank=True)


class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
    images = models.ManyToManyField(StoryPics, blank=True, related_name="stories")
    videos = models.ManyToManyField(StoryVideos, blank=True, related_name="stories")
    show_to_close_friends = models.BooleanField(default=False)