from django.contrib import admin
from django.urls import path
from . import admin_manage_views as views
app_name = 'admin_manage'

urlpatterns = [
    path('home/',views.get_admin_manage_page,name="admin_home")
]