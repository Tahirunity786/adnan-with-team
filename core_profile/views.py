
# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from core_post.models import Like, Save, UserPost, archive
from core_profile.serializers import (UserSerializer, UserdSerializer, GetProfileSerializer, UserProfileUpdateSerializer, SaveSerializer, StorySerializer)
from core_post.serializers import ArchievedSerializer, UserPostSerializer, LikedSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import GetProfileSerializer
from core_post.models import UserPost
from core_profile.models import Story, StoryPics, StoryVideos
from rest_framework import generics, permissions
from django.db.models import Q
User = get_user_model()

class Profile(APIView):
    """
    API endpoint to retrieve user profile details including followers, following, and posts.

    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve user profile details.

        Returns:
            Response: JSON response containing user profile details, followers, following, and posts.
        """

        try:
            # Retrieve authenticated user
            user = User.objects.get(id=request.user.id)
            # Serialize user profile
            profile_serializer = GetProfileSerializer(user)

            # Calculate the number of followers and following
            followers_count = user.followers.count()
            following_count = user.following.count()

            # Retrieve user posts
            posts = UserPost.objects.filter(user=user).order_by("-id")

            # Serialize user posts
            post_serializer = UserPostSerializer(posts, many=True)

            # Serialize followers and following
            user_follower = [{"id": follower.id, "username": follower.username} for follower in user.followers.all()]
            user_following = [{"id": following.id, "username": following.username} for following in user.following.all()]

            # Prepare response data
            response = {
                'user_data': profile_serializer.data,
                'follow_data': {
                    'followers_count': followers_count,
                    'following_count': following_count,
                    'user_followers': user_follower,
                    'user_following': user_following
                },
                'user_posts': {
                    "post_count": posts.count(),
                    "post_data": post_serializer.data,
                }  # Serialized posts data
            }
            return Response(response, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class Get_Profile(APIView):
    """
    API endpoint to retrieve user profile details including followers, following, and posts.
    By an id

    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve user profile details.

        Returns:
            Response: JSON response containing user profile details, followers, following, and posts.
        """

        try:
            # Get the user id to get profile
            user_id = request.data.get("user_id")
            # Retrieve authenticated user
            user = User.objects.get(id=user_id)

            # If the user has a private account, only show limited information to non-followers
            if user.account_mode == 'Private' and user != request.user:
                # Calculate the number of followers and following
                followers_count = user.followers.count()
                following_count = user.following.count()

                # Prepare response data
                response = {
                    'user_data': {
                        'id': user.id,
                        'full_name': user.full_name,
                        'username': user.username,
                        'profile': user.profile.url if user.profile else None,
                        'profile_slug': user.profile_slug,
                        'profile_info': user.profile_info,
                        'is_private': True,
                        'followers_count': followers_count,
                        'following_count': following_count,
                    }
                }
                return Response(response, status=status.HTTP_200_OK)

            # Serialize user profile
            profile_serializer = GetProfileSerializer(user)

            # Calculate the number of followers and following
            followers_count = user.followers.count()
            following_count = user.following.count()

            # Retrieve user posts
            posts = UserPost.objects.filter(user=user).order_by("-id")

            # Serialize user posts
            post_serializer = UserPostSerializer(posts, many=True)

            # Serialize followers and following
            user_follower = [{"id": follower.id, "username": follower.username} for follower in user.followers.all()]
            user_following = [{"id": following.id, "username": following.username} for following in user.following.all()]

            # Prepare response data
            response = {
                'user_data': profile_serializer.data,
                'follow_data': {
                    'followers_count': followers_count,
                    'following_count': following_count,
                    'user_followers': user_follower,
                    'user_following': user_following
                },
                'user_posts': {
                    "post_count": posts.count(),
                    "post_data": post_serializer.data,
                }  # Serialized posts data
            }
            return Response(response, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class Share_profile(APIView):
    """
    API endpoint to share a user profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        """
        Retrieve and serialize the user profile.

        Parameters:
        - request: The HTTP request object.
        - kwargs: Keyword arguments containing the user profile slug.

        Returns:
        - Response containing the serialized user profile data or error message.
        """
        try:
            slug = kwargs.get('slug')
            post = UserPost.objects.get(post_slug=slug)

            # Serialize the post
            post_data = UserPostSerializer(post)
            return Response(post_data.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FollowUser(APIView):
    """
    API endpoint to allow a user to follow another user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Follow a user.

        Parameters:
        - request: The HTTP request object containing user_id of the user to follow.

        Returns:
        - Response indicating success or failure of the operation.
        """
        serializer = UserdSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user_to_follow = User.objects.get(id=user_id)
                user = request.user

                # Check if the user is already following user_to_follow
                if user.following.filter(id=user_to_follow.id).exists():
                    return Response({'error': 'You are already following this user'}, status=status.HTTP_400_BAD_REQUEST)

                user.following.add(user_to_follow)
                return Response({"success": f"{user} is now following {user_to_follow}"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnfollowUser(APIView):
    """
    API endpoint to allow a user to unfollow another user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Unfollow a user.

        Parameters:
        - request: The HTTP request object containing user_id of the user to unfollow.

        Returns:
        - Response indicating success or failure of the operation.
        """
        serializer = UserdSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user_to_unfollow = User.objects.get(id=user_id)
                user = request.user
                user.following.remove(user_to_unfollow)
                return Response({"Success":f"user {user} unfollow the user {user_to_unfollow.full_name}"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowersList(APIView):
    """
    API endpoint to retrieve the list of followers for a user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve and serialize the list of followers for the authenticated user.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - Response containing the serialized list of followers.
        """
        user = request.user
        followers = user.followers.all()
        serializer = UserSerializer(followers, many=True)
        return Response(serializer.data)


class FollowingList(APIView):
    """
    API endpoint to retrieve the list of users being followed by a user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve and serialize the list of users being followed by the authenticated user.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - Response containing the serialized list of users being followed.
        """
        user = request.user
        following = user.following.all()
        serializer = UserSerializer(following, many=True)
        return Response(serializer.data)

class UpdateProfile(APIView):
    """
    API endpoint to allow users to update their profiles.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Update the profile of the authenticated user.

        Request Data:
        {
            "full_name": "New Full Name",
            "email": "new@example.com",
            "date_of_birth": "1990-01-01",
            "mobile_number": "1234567890",
            "profile_info": "New profile information"
            "interest": User able to add interest such as sports, gaming etc
            # Include any other fields you want to update
        }
        """
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Close_friend(APIView):
    """
    API view to add a user as a close friend.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        POST method to add a user as a close friend.

        Args:
            request (Request): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Response object with success or error message.

        Raises:
            NotFound: If the user with the provided user_id does not exist.
        """
        serializer = UserdSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user_close_friend = User.objects.get(id=user_id)
                user = request.user
                # Check if the user is already following user_to_follow
                if user.close_friends.filter(id=user_close_friend.id).exists():
                    return Response({'error': 'You are already close friend of this user'}, status=status.HTTP_400_BAD_REQUEST)
                user.close_friends.add(user_close_friend)
                return Response({"success": f"{user} is now close friend of {user_close_friend}"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CloseFriendList(APIView):
    """
    API view to retrieve the list of close friends for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        GET method to retrieve the list of close friends.

        Args:
            request (Request): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Response object with the list of close friends.

        """
        user = request.user
        friends = user.close_friends.all()
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data)

class ReCloseFriend(APIView):
    """
    API endpoint to remove a user from the current user's close friends list.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to remove a user from close friends list.

        Parameters:
        - request: HTTP request object
        - *args: Additional positional arguments
        - **kwargs: Additional keyword arguments

        Returns:
        - Response: HTTP response indicating success or failure
        """
        serializer = UserdSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                user_close_friend = User.objects.get(id=user_id)
                user = request.user
                user.close_friends.remove(user_close_friend)
                return Response(status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavedPostList(generics.ListAPIView):
    """
    API endpoint to list all saved posts of the authenticated user.
    """
    serializer_class = SaveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve saved posts queryset for the authenticated user.

        Returns:
        - QuerySet: QuerySet of saved posts for the authenticated user
        """
        user = self.request.user
        return Save.objects.filter(user=user).order_by("-id")


class likePostList(generics.ListAPIView):
    """
    API endpoint to list all liked posts of the authenticated user.
    """
    serializer_class = LikedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve liked posts queryset for the authenticated user.

        Returns:
        - QuerySet: QuerySet of liked posts for the authenticated user
        """
        user = self.request.user
        return Like.objects.filter(user=user).order_by("-id")


class ArchievedPostList(generics.ListAPIView):
    """
    API endpoint to list all archived posts of the authenticated user.
    """
    serializer_class = ArchievedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve archived posts queryset for the authenticated user.

        Returns:
        - QuerySet: QuerySet of archived posts for the authenticated user
        """
        user = self.request.user
        return archive.objects.filter(user=user).order_by("-id")

class AddStoryView(APIView):
    """
    API endpoint for adding a story by a specific user.

    Permissions:
        - User must be authenticated.

    Request Method:
        - POST

    Request Payload:
        - images: List of image files for the story (optional).
        - videos: List of video files for the story (optional).

    Response:
        - HTTP 201 Created: If the story is successfully added.
        - HTTP 400 Bad Request: If the request payload is invalid or incomplete.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Method to add a story for a specific user.

        Args:
            request (HttpRequest): HTTP request object.

        Returns:
            Response: JSON response indicating success or failure.
        """
        user = request.user
        images = request.data.getlist("images")
        videos = request.data.getlist("videos")
        is_show_to_close_friends = request.data.get("show_to_close_friends")


        # Ensure at least one of images or videos is provided
        if not images and not videos:
            return Response({"error": "Either images or videos are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the story object
        story = Story.objects.create(user=user)

        if is_show_to_close_friends:
            story.show_to_close_friends = True

        # Handle images
        for img in images:
            story_pic = StoryPics.objects.create(image=img)
            story.images.add(story_pic)

        # Handle videos
        for vid in videos:
            story_video = StoryVideos.objects.create(video=vid)
            story.videos.add(story_video)

        return Response(StorySerializer(story).data, status=status.HTTP_201_CREATED)

class StoryView(APIView):
    """
    API endpoint to show stories based on user's privacy settings and relationships.
    """

    def get(self, request):
        """
        Method to get stories based on user's privacy settings and relationships.

        Args:
            request (HttpRequest): HTTP request object.

        Returns:
            Response: JSON response containing stories.
        """
        user = request.user
        # Retrieve stories based on the user's account mode
        if user.account_mode == "Public":
            stories = Story.objects.all()
        else:  # Private mode
            # Retrieve stories visible to close friends
            close_friends_stories = Story.objects.filter(user__in=user.close_friends.all()).order_by("-id")
            # Retrieve stories that are public
            public_stories = Story.objects.filter(user__account_mode="Public").order_by("-id")
            # Combine close friends' stories and public stories
            stories = close_friends_stories | public_stories

        # Exclude stories from muted people and blocked users
        stories = stories.exclude(user__in=user.mute_peoples.all()).exclude(user__in=user.blockel_peoples.all())

        serializer = StorySerializer(stories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteStoryView(APIView):
    """
    API endpoint to delete stories created by the user.
    """

    def post(self, request):
        """
        Method to delete a story created by the user.

        Args:
            request (HttpRequest): HTTP request object containing the story ID in the request payload.

        Returns:
            Response: JSON response indicating success or failure.
        """
        user = request.user
        story_id = request.data.get('story_id')

        if not story_id:
            return Response({"error": "Story ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the story
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response({"error": "Story not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the creator of the story
        if story.user != user:
            return Response({"error": "You are not authorized to delete this story"}, status=status.HTTP_403_FORBIDDEN)

        # Delete the story
        story.delete()
        return Response({"message": "Story deleted successfully"}, status=status.HTTP_204_NO_CONTENT)