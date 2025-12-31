from django.contrib import admin
from django.urls import path
from . import pomodoro_views as views
app_name = 'pomodoro'

urlpatterns = [

    path('', views.pomodoro_home, name='home'),
    path('<str:pomodoro_id>/', views.pomodoro_detail, name='detail'),
    path('history/', views.pomodoro_history, name='history'),
    
    # API endpoints
    path('api/create/', views.api_create_pomodoro, name='api_create'),
    path('api/start/', views.api_start_pomodoro, name='api_start'),
    path('api/pause/', views.api_pause_pomodoro, name='api_pause'),
    path('api/stop/', views.api_stop_pomodoro, name='api_stop'),
    path('api/complete/', views.api_complete_session, name='api_complete'),
    path('api/settings/update/', views.api_update_settings, name='api_update_settings'),
    path('api/status/<str:pomodoro_id>/', views.api_get_pomodoro_status, name='api_status'),
    path('api/statistics/', views.api_get_statistics, name='api_statistics'),
    path('api/history/<str:history_id>/delete/', views.api_delete_history, name='api_delete_history'),

]