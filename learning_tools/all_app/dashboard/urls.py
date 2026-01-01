# all_app/dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('api/settings/update/', views.update_widget_settings, name='update_settings'),
    path('api/quick-stats/', views.get_quick_stats, name='quick_stats'),
    path('api/quick-add-task/', views.quick_add_task, name='quick_add_task'),
    path('api/update-habit/<int:habit_id>/', views.update_habit_status, name='update_habit'),
    path('api/recent-activity/', views.get_recent_activity, name='recent_activity'),
]