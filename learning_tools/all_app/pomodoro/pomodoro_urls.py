from django.contrib import admin
from django.urls import path
from . import pomodoro_views as views
app_name = 'pomodoro'

urlpatterns = [

    path('home', views.pomodoro_home, name='home'),
    path('<str:pomodoro_id>/', views.pomodoro_detail, name='detail'),
    path('history/', views.pomodoro_history, name='history'),
    
    # API endpoints
    path('home/create/', views.api_create_pomodoro, name='api_create'),
    path('home/start/', views.api_start_pomodoro, name='api_start'),
    path('home/pause/', views.api_pause_pomodoro, name='api_pause'),
    path('home/update-timer/', views.api_update_timer, name='api_update_timer'),
    path('home/stop/', views.api_stop_pomodoro, name='api_stop'),
    path('home/complete/', views.api_complete_session, name='api_complete'),
    path('home/settings/update/', views.api_update_settings, name='api_update_settings'),
    path('home/update-duration/', views.api_update_duration, name='api_update_duration'),
    path('home/status/<str:pomodoro_id>/', views.api_get_pomodoro_status, name='api_status'),
    path('home/statistics/', views.api_get_statistics, name='api_statistics'),
    path('home/history/<str:history_id>/delete/', views.api_delete_history, name='api_delete_history'),

]