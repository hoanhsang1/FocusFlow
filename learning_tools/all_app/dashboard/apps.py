# all_app/dashboard/apps.py
from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'all_app.dashboard'  # QUAN TRỌNG: Đây phải khớp với INSTALLED_APPS
    verbose_name = 'Dashboard'