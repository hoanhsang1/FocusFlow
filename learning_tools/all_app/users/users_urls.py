from django.contrib import admin
from django.urls import path
from . import users_views as views
app_name = 'users'

urlpatterns = [
    path('login/',views.show_login, name='login_form'),
    path('login/submit/', views.check_login, name='login_form-post'),
    path('register/submit/', views.register_user, name='register_form-post'),
    path('register/',views.show_register, name='register_form'),
    # Google OAuth URLs
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # API URLs (AJAX)
    path('api/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('api/user-info/', views.get_user_info, name='get_user_info'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
]