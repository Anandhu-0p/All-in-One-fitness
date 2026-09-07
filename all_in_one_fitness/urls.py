from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('users/', include('users.urls')),
    path('trainers/', include('trainers.urls')),
    path('experts/', include('experts.urls')),
    path('fitness/', include('fitness.urls')),
    path('payments/', include('payments.urls')),
    path('events/', include('events.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)