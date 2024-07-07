from django.urls import path, include
from rest_framework import routers
from core_post.views import (SocialPOST,SharePostAPIView,  UserPostCreateView, UserPostDeleteView, UserPostUpdateView, LikeDeleteView, CommentCreateView, CommentsonCommentCreateView, UserPostFavoriteView, UserPostFavoriteDeleteView, LikeCreateView, SavePostView, UnsavePostView, UserSearchPostAPIView, ArchieveCreateView)

# Create a router for handling viewsets
router = routers.DefaultRouter()
router.register(r'public/posts', SocialPOST, basename='socialpost')  # Specify basename


# URL patterns for various endpoints
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Endpoint for creating a new user post
    path("public/post/create", UserPostCreateView.as_view(), name="new-post-create"),

    # Endpoint for deleting a user post
    path("public/post/delete", UserPostDeleteView.as_view(), name="new-post-delete"),

    # Endpoint for updating a user post
    path("public/post/update", UserPostUpdateView.as_view(), name="new-post-update"),

    # Endpoint for deleting a favorite post
    path("public/post/favourite/delete", UserPostFavoriteDeleteView.as_view(), name="post-fave-del"),

    # Endpoint for marking a post as favorite
    path("public/post/favourite/create", UserPostFavoriteView.as_view(), name="post-fave"),

    # Endpoint for creating comments on comments
    path("public/post/comments-on-comments", CommentsonCommentCreateView.as_view(), name="comments-on-comments"),

    # Endpoint for creating a comment on a post
    path("public/post/comment", CommentCreateView.as_view(), name="comments"),

    # Endpoint for liking a post
    path("public/post/like", LikeCreateView.as_view(), name="post-like"),

    # Endpoint for unliking a post
    path("public/post/like/delete", LikeDeleteView.as_view(), name="post-like-delete"),

    # Endpoint for saving a post
    path("public/post/save", SavePostView.as_view(), name="post-save"),

    # Endpoint for unsaving a post
    path("public/post/save/delete", UnsavePostView.as_view(), name="post-save-del"),

    # Endpoint for searching posts
    path("public/post/search", UserSearchPostAPIView.as_view(), name="post-search"),

    # Endpoint for archiving a post
    path("public/post/archive", ArchieveCreateView.as_view(), name="post-archive"),

    # Endpoint for Share a post
    path('public/post/share/<slug:post_slug>/', SharePostAPIView.as_view(), name='share_post'),
]
