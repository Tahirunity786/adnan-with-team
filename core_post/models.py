from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid
User = get_user_model()


class Topics(models.Model):
    topic = models.CharField(max_length=200, default="", db_index=True)


# Create your models here.
class PostVideoMedia(models.Model):
    """
    Model to represent videos associated with posts.
    """
    video = models.FileField(upload_to="post_videos",
                             verbose_name="Post Video")


class PostImageMedia(models.Model):
    """
    Model to represent images associated with posts.
    """
    image = models.ImageField(upload_to='post_images/',
                              verbose_name="Post Image")


class UserPost(models.Model):
    """
    Model to represent user-created posts.
    """
    # Is show to Everyone and close friends
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="posts_created", blank=True, null=True)
    post_slug = models.SlugField(unique=True, default="")
    images = models.ManyToManyField(PostImageMedia, related_name="posts")
    videos = models.ManyToManyField(
        PostVideoMedia, related_name="postsvideos", blank=True)
    title = models.CharField(max_length=150, db_index=True)
    description = models.TextField(verbose_name="Post Description")
    date = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    is_archieved = models.BooleanField(default=False)
    show_to_close_friends = models.BooleanField(default=False)
    tagged = models.ManyToManyField(User, related_name="peoples")
    Is_allow_comment = models.BooleanField(default=True)
    add_topics = models.ManyToManyField(Topics, blank=True, default="")
    hide_likes = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    share_count = models.IntegerField(default=0)
    shared_by = models.ManyToManyField(User, related_name="share")
    share_privacy = models.BooleanField(default=False)

    def __str__(self):
        """
        String representation of the UserPost object.
        """
        return self.title

    def save(self, *args, **kwargs):
        """
        Custom save method to auto-generate post_slug from username.
        If the post_slug already exists, append a UUID to make it unique.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        if not self.post_slug:
            # Generate post slug from title
            self.post_slug = slugify(self.title)

        # Check if post_slug already exists
        if UserPost.objects.filter(post_slug=self.post_slug).exists():
            # Append UUID to make it unique
            self.post_slug += f"-{uuid.uuid4().hex[:8]}"

        super().save(*args, **kwargs)

    def can_update_post(self):
        """
        Check if the post can be updated.
        """
        return (
            self.is_published
            and not self.is_archieved
            and self.allow_comments
            and not self.is_draft
        )

    class Meta:
        verbose_name_plural = "User Posts"


class Like(models.Model):
    """
    Represents a like on a user post.

    Attributes:
        user (User): The user who liked the post.
        post (UserPost): The post that was liked.
        date_time (DateTimeField): The date and time when the like was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE)
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "post"),)


class Favorite(models.Model):
    """
    Represents a favorite post by a user.

    Attributes:
        user (User): The user who favorited the post.
        post (UserPost): The post that was favorited.
        date_time (DateTimeField): The date and time when the post was favorited.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE)
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "post"),)


class Comment(models.Model):
    """
    Represents a comment on a user post.

    Attributes:
        user (User): The user who posted the comment.
        post (UserPost): The post on which the comment was posted.
        content (TextField): The content of the comment.
        timestamp (DateTimeField): The date and time when the comment was posted.
        parent_comment (Comment): The parent comment if this comment is a reply to another comment.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(
        UserPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')


class Save(models.Model):
    """
    Represents a saved post by a user.

    Attributes:
        user (User): The user who saved the post.
        post (UserPost): The post that was saved.
        date_time (DateTimeField): The date and time when the post was saved.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE)
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "post"),)


class archive(models.Model):
    """
    Represents an archived post by a user.

    Attributes:
        user (User): The user who archived the post.
        post (UserPost): The post that was archived.
        date_time (DateTimeField): The date and time when the post was archived.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE)
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "post"),)
