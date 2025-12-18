from django.contrib import admin
from django.urls import path
from . import to_do_list_views as views
app_name = 'to_do_list'

urlpatterns = [
    path('home/',views.get_home, name='home'),
    path('add_group/', views.add_group, name='add_group'),
    path('edit_group/<str:groupID>/', views.edit_group, name='edit_group'),
    path('get_tasks/<str:group_id>/', views.get_tasks, name='get_tasks'),
    path('search_groups/', views.search_groups, name='search_groups'),
    path('get_taskInfo/<str:taskID>/', views.get_taskInfo, name='get_taskinfo'),
    path('get_taskInfo/edit_taskInfo/<str:taskID>/', views.edit_taskInfo, name='edit_taskInfo'),
    path('get_taskInfo/soft_delete_task/<str:taskID>/', views.soft_delete_task, name='soft_delete_task'),
    path('add_task/<str:group_id>/', views.add_task, name='add_task'),
    path('change_status/<str:task_id>/', views.change_status, name='change_status'),
]