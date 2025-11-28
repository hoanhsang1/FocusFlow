from django.contrib import admin
from django.urls import path
from . import admin_manage_views as views
app_name = 'admin_manage'

urlpatterns = [
    path('dashboard/', views.admin_manage_dashboard, name='admin_manage_dashboard'),
    path('users/', views.admin_manage_users, name='admin_manage_users'),
    path('groups/', views.admin_manage_groups, name='admin_manage_groups'),
    path('tasks/', views.admin_manage_tasks, name='admin_manage_tasks'),
    path('system/', views.admin_manage_system, name='admin_manage_system'),
    path('analytics/', views.admin_manage_analytics, name='admin_manage_analytics'),
]