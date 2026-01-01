"""
URL configuration for learning_tools project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('all_app.dashboard.urls')),
    path('calendar/', include('all_app.calendar_app.calendar_urls')),
    path('flashcards/', include('all_app.flashcards.flashcards_urls')),
    path('habit/', include('all_app.habit.habit_urls')),
    path('pomodoro/', include('all_app.pomodoro.pomodoro_urls')),
    path('todolist/', include('all_app.to_do_list.to_do_list_urls')),
    path('users/', include('all_app.users.users_urls')),
    path('admin_manage/', include('all_app.admin_manage.admin_manage_urls')),
]

# QUAN TRỌNG: Thêm cả static và media
if settings.DEBUG:
    # Static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# HOẶC nếu bạn dùng STATICFILES_DIRS:
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)