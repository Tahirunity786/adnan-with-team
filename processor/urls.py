from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('social-media/', include('core_account.urls')),
    path('social-post/', include('core_post.urls')),
    path('social-profile/', include('core_profile.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
