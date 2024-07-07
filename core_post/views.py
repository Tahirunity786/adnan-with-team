from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core_post.models import Comment, Favorite, Like, Save, User, UserPost
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.views import Response
from core_post.models import UserPost
from core_post.serializers import (SharePostSerializer, ArchieveSerializer, SocialPostSerializer, CommentSerializer, RCommentSerializer, FavoriteSerializer,
                                   LikeSerializer, PostImageMediaSerializer, PostVideoMediaSerializer, SaveSerializer, UnsaveSerializer, UserPostSerializer, UserPostSerializer)
from django.db.models import Count
from core_post.models import archive
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
# Create your views here.


# ======================================= POST SECTION # ======================================= #

class SocialPOST(viewsets.ModelViewSet):
    """
    A ViewSet for handling Logic to show  posts.
    """
    serializer_class = SocialPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        interests = user.Interest.all()

        # If the user has no interests, show all posts
        if not interests.exists():
            return UserPost.objects.all().order_by('-date')

        # Get posts matching user interests
        queryset = UserPost.objects.filter(
            Q(is_published=True) & ~Q(add_topics__in=interests) &
            Q(is_archieved=False) & Q(is_draft=False)
        )

        # Add posts by followed users
        followed_users_posts = UserPost.objects.filter(
            user__in=user.following.all(),
            is_published=True,
            is_archieved=False,
            is_draft=False
        )
        queryset = queryset | followed_users_posts

        # Add popular posts based on likes and comments
        popular_posts = UserPost.objects.filter(
            is_published=True,
            is_archieved=False,
            is_draft=False
        ).annotate(
            total_likes=Count('like'),
            total_comments=Count('comment')
        ).order_by('-total_likes', '-total_comments')[:100]  # Adjust this limit as needed
        queryset = queryset | popular_posts

        # Show all posts if the user has a new account
        if user.date_joined > timezone.now() - timedelta(days=7):  # Adjust the timeframe as needed
            queryset = UserPost.objects.all().order_by('-date')

        # Annotate queryset with count of likes
        queryset = queryset.annotate(total_likes=Count('like'))

        # Order queryset by date
        queryset = queryset.order_by('-date').distinct()

        return queryset

class UserPostCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a new user post.
    """

    queryset = UserPost.objects.all()
    serializer_class = UserPostSerializer  # This is the serializer_class attribute
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    allowed_methods = ['POST']  # Allow only POST method

    def create(self, request, *args, **kwargs):
        # Extract image, video, tagged, and topics data from request
        image_data = request.data.getlist('images')
        video_data = request.data.getlist('videos')
        tagged_data = request.data.getlist('tagged')
        topics_data = request.data.getlist('add_topics')

        # Add the user to the request data
        request.data['user'] = request.user.id

        # Create post object
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():  # Ensure atomicity of the operations
                self.perform_create(serializer)

                # Save associated images
                for image_item in image_data:
                    image_serializer = PostImageMediaSerializer(
                        data={'image': image_item})
                    if image_serializer.is_valid():
                        image_serializer.save()
                        serializer.instance.images.add(
                            image_serializer.instance)

                # Save associated videos
                for video_item in video_data:
                    video_serializer = PostVideoMediaSerializer(
                        data={'video': video_item})
                    if video_serializer.is_valid():
                        video_serializer.save()
                        serializer.instance.videos.add(
                            video_serializer.instance)

                # Save tagged users
                serializer.instance.tagged.set(tagged_data)

                # Save topics
                serializer.instance.add_topics.set(topics_data)

        except Exception as e:
            # Rollback transaction in case of error
            transaction.rollback()

            # Return error response
            return Response({"error": f"An error occurred while saving the post. {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # If everything is successful, return the response
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserPostDeleteView(APIView):
    """
    API endpoint for deleting a user post.
    """

    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, *args, **kwargs):
        # Ensure that the request user is the owner of the post
        # Assuming you pass post_id in request data
        post_id = request.data.get('post_id')
        try:
            post = UserPost.objects.get(id=post_id, user=request.user)
        except UserPost.DoesNotExist:
            return Response({"error": "Post not found or you don't have permission to delete it."},
                            status=status.HTTP_404_NOT_FOUND)

        post.delete()
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class UserPostUpdateView(APIView):
    """
    API endpoint for updating a user post.
    """

    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request):
        """
        Handle POST requests for updating a user post.

        Allows users to update their specific post including images and videos.

        Returns a response with the updated post data.
        """

        # Retrieve the post instance
        post_id = request.data.get('post_id')
        try:
            post = UserPost.objects.get(id=post_id, user=request.user)
        except UserPost.DoesNotExist:
            return Response({"error": "Post not found or you don't have permission to update it."},
                            status=status.HTTP_404_NOT_FOUND)

        # Extract image and video data from request
        image_data = request.data.getlist('images')
        video_data = request.data.getlist('videos')

        # Update post data
        serializer = UserPostSerializer(instance=post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Update associated images
        for image_item in image_data:
            image_serializer = PostImageMediaSerializer(
                data={'image': image_item})
            if image_serializer.is_valid():
                image_serializer.save()
                post.images.add(image_serializer.instance)

        # Update associated videos
        for video_item in video_data:
            video_serializer = PostVideoMediaSerializer(
                data={'video': video_item})
            if video_serializer.is_valid():
                video_serializer.save()
                post.videos.add(video_serializer.instance)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LikeCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a like on a post.
    """

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    allowed_methods = ['POST']  # Allow only POST method

    def create(self, request, *args, **kwargs):
        """
        Handle POST requests for creating a like on a post.

        Returns a response with the created like data.
        """

        # Extract post ID from request data
        post_id = request.data.get('post_id')

        # Check if the post exists
        try:
            post = UserPost.objects.get(pk=post_id)
        except UserPost.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already liked the post
        if Like.objects.filter(user=request.user, post=post).exists():
            return Response({"error": "You have already liked this post."}, status=status.HTTP_400_BAD_REQUEST)

        # Create like
        serializer = self.get_serializer(
            data={'user': request.user.id, 'post': post_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Increment post's likes count
        post.likes_count += 1
        post.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LikeDeleteView(generics.DestroyAPIView):
    """
    API endpoint for deleting a like on a post.
    """

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for deleting a like on a post.

        Returns a response indicating success.
        """

        # Extract like ID from URL kwargs
        like_id = request.data.get('like_id')

        # Check if the like exists
        try:
            like = Like.objects.get(pk=like_id)
        except Like.DoesNotExist:
            return Response({"error": "Like not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the owner of the like
        if like.user != request.user:
            return Response({"error": "You don't have permission to delete this like."},
                            status=status.HTTP_403_FORBIDDEN)

        # Decrement post's likes count
        post = like.post
        post.likes_count -= 1
        post.save()

        # Delete like
        like.delete()

        return Response({"message": "Like deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class UserPostFavoriteView(generics.CreateAPIView):
    """
    API endpoint for favoriting a post.
    """
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def create(self, request, *args, **kwargs):
        """
        Handle POST requests for favoriting a post.

        Allows authenticated users to favorite a post.

        Returns a response indicating the success of the operation.
        """
        user = request.user
        post_id = request.data.get('post_id')
        try:
            post = UserPost.objects.get(pk=post_id)
        except UserPost.DoesNotExist:
            return Response({"error": "Post does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the post is already favorited by the user
        if Favorite.objects.filter(user=user, post=post).exists():
            return Response({"message": "Post is already favorited by the user."}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite(user=user, post=post)
        favorite.save()
        return Response({"message": "Post favorited successfully."}, status=status.HTTP_201_CREATED)


class UserPostFavoriteDeleteView(APIView):
    """
    API endpoint for deleting a favorite post.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for deleting a favorite post.

        Allows authenticated users to delete their own favorite post.

        Returns a response indicating the success of the operation.
        """
        user = request.user
        favorite_id = request.data.get('favorite_id')

        try:
            favorite = Favorite.objects.get(pk=favorite_id)
        except Favorite.DoesNotExist:
            return Response({"error": "Favorite post does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the creator of the favorite
        if favorite.user != user:
            return Response({"error": "You are not authorized to delete this favorite post."},
                            status=status.HTTP_403_FORBIDDEN)

        favorite.delete()
        return Response({"message": "Favorite post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class CommentCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a comment on a post.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def create(self, request):
        """
        Handle POST requests for creating a comment on a post.

        Allows authenticated users to create comments on posts.

        Returns a response with the created comment data.
        """

        # Extract post id from the request data
        post_id = request.data.get('post_id')

        # Check if the post exists
        try:
            post = UserPost.objects.get(id=post_id)
        except UserPost.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the post allows comments
        if post.Is_allow_comment:
            return Response({"error": f"Comments are not allowed on this post. {post.Is_allow_comment}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the commenting user is muted by the post creator
        if post.user.mute_peoples.filter(id=request.user.id).exists():
            return Response({"error": "You are muted by the post creator."}, status=status.HTTP_403_FORBIDDEN)

        # Create a new comment
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Store the requesting user in the serializer's context
        serializer.context['user'] = request.user

        serializer.save(user=request.user, post=post)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentsonCommentCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a comment on a post or on another comment.
    """

    serializer_class = RCommentSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    allowed_methods = ['POST']  # Allow only POST method

    def create(self, request):
        """
        Handle POST requests for creating a comment on a post or on another comment.

        Allows authenticated users to create comments on posts or on another comment.

        Returns a response with the created comment data.
        """

        # Extract post id and parent comment id from the request data
        post_id = request.data.get('post_id')
        parent_comment_id = request.data.get('parent_comment_id', None)

        # Check if the post exists
        try:
            post = UserPost.objects.get(id=post_id)
        except UserPost.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the parent comment exists
        if parent_comment_id:
            try:
                parent_comment = Comment.objects.get(id=parent_comment_id)
            except Comment.DoesNotExist:
                return Response({"error": "Parent comment not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            parent_comment = None

        # Create a new comment
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, post=post,
                        parent_comment=parent_comment)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SavePostView(APIView):
    """
    API endpoint for saving a post.
    """

    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for saving a post.

        Allows users to save a specific post.

        Returns a response with the saved post data.
        """

        user = request.user
        # Assuming post_id is passed in request data
        post_id = request.data.get('post_id')

        try:
            # Check if the post is already saved by the user
            Save.objects.get(user=user, post_id=post_id)
            return Response({"message": "Post already saved by the user."}, status=status.HTTP_400_BAD_REQUEST)
        except Save.DoesNotExist:
            pass

        # Save the post
        serializer = SaveSerializer(data={'user': user.id, 'post': post_id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnsavePostView(APIView):
    """
    API endpoint for unsaving a post.
    """

    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for unsaving a post.

        Allows users to unsave a specific post.

        Returns a response indicating success or failure of the unsaving process.
        """

        user = request.user

        # Validate the post_id
        serializer = UnsaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post_id = serializer.validated_data['post_id']

        try:
            # Check if the post is saved by the user
            saved_post = Save.objects.get(user=user, post_id=post_id)
            saved_post.delete()
            return Response({"message": "Post unsaved successfully."}, status=status.HTTP_200_OK)
        except Save.DoesNotExist:
            return Response({"error": "Post is not saved by the user."}, status=status.HTTP_400_BAD_REQUEST)


class UserSearchPostAPIView(APIView):
    """
    A custom API view to search posts based on title or description.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves posts based on a search query.

        Parameters:
        - query (str): The search query string.

        Returns:
        - Response: JSON response containing the serialized search results.

        Raises:
        - HTTP 400 Bad Request: If the 'query' parameter is missing.
        """
        # Retrieve the search query from request data
        query = request.data.get('query', None)

        # Check if query parameter is provided
        if not query:
            return Response({'error': 'Query parameter "query" is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Search posts based on title or description containing the query string
        posts = UserPost.objects.filter(
            title__icontains=query) | UserPost.objects.filter(description__icontains=query).order_by("-id")

        # Serialize the search results
        serializer = UserPostSerializer(posts, many=True)

        # Return the serialized data as JSON response
        return Response(serializer.data)


class ArchieveCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a like on a post.
    """

    serializer_class = ArchieveSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    allowed_methods = ['POST']  # Allow only POST method

    def create(self, request, *args, **kwargs):
        """
        Handle POST requests for creating a like on a post.

        Returns a response with the created like data.
        """

        # Extract post ID from request data
        post_id = request.data.get('post_id')

        # Check if the post exists
        try:
            post = UserPost.objects.get(pk=post_id)
        except:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already liked the post
        if archive.objects.filter(user=request.user, post=post).exists():
            return Response({"error": "You have already Archived this post."}, status=status.HTTP_400_BAD_REQUEST)

        # Create like
        serializer = self.get_serializer(
            data={'user': request.user.id, 'post': post_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Increment post's likes count
        post.is_archieved = True
        post.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SharePostAPIView(APIView):
    """
    API endpoint to share a post by an authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, post_slug):
        """
        Share a post by an authenticated user.

        Parameters:
        - request: The HTTP request object.
        - post_slug (str): The slug of the post to be shared.

        Returns:
        - Response: A JSON response indicating success or failure.
        """
        try:
            # Get the post to be shared
            post = UserPost.objects.get(post_slug=post_slug, is_archieved=False, is_published=True)

            # Check if the post is already shared by the user
            if request.user not in post.shared_by.all():
                # Increase the share count
                post.share_count += 1
                post.shared_by.add(request.user)
                post.save()

            else:
                post.share_count += 1
                post.save()



            serializer = SharePostSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UserPost.DoesNotExist:
            return Response({"error": "Post not found or cannot be shared"}, status=status.HTTP_404_NOT_FOUND)
