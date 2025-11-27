from django.contrib import admin
from django.urls import path
from . import to_do_list_views as views
app_name = 'to_do_list'

urlpatterns = [
    path('home/',views.get_home, name='home'),
    path('add_group/', views.add_group, name='add_group'),
    path('get_tasks/<str:group_id>/', views.get_tasks, name='get_tasks'),
    path('add_task/<str:group_id>/', views.add_task, name='add_task'),
    path('change_status/<str:task_id>/', views.change_status, name='change_status'),
]