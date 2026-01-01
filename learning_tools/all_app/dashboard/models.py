# all_app/dashboard/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DashboardSettings(models.Model):
    """Cài đặt dashboard của người dùng"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_settings')
    
    # Cấu hình widget
    layout_config = models.JSONField(default=dict, help_text="Cấu hình vị trí các widget")
    
    # Hiển thị widget
    show_pomodoro = models.BooleanField(default=True)
    show_todo = models.BooleanField(default=True)
    show_calendar = models.BooleanField(default=True)
    show_habits = models.BooleanField(default=True)
    show_flashcards = models.BooleanField(default=True)
    show_productivity = models.BooleanField(default=True)
    
    # Thứ tự widget
    widget_order = models.JSONField(default=list, help_text="Thứ tự các widget")
    
    # Theme
    theme = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Light Mode'),
            ('dark', 'Dark Mode'),
            ('auto', 'Auto (System)')
        ],
        default='light'
    )
    
    # Cập nhật
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard Settings - {self.user.username}"
    
    def get_widgets(self):
        """Lấy danh sách widget đã kích hoạt"""
        widgets = []
        if self.show_pomodoro:
            widgets.append('pomodoro')
        if self.show_todo:
            widgets.append('todo')
        if self.show_calendar:
            widgets.append('calendar')
        if self.show_habits:
            widgets.append('habits')
        if self.show_flashcards:
            widgets.append('flashcards')
        if self.show_productivity:
            widgets.append('productivity')
        
        # Sắp xếp theo thứ tự đã lưu
        if self.widget_order:
            widgets.sort(key=lambda x: self.widget_order.index(x) if x in self.widget_order else 999)
        
        return widgets

class UserActivity(models.Model):
    """Lưu lịch sử hoạt động của người dùng"""
    ACTIVITY_TYPES = [
        ('pomodoro_start', 'Bắt đầu Pomodoro'),
        ('pomodoro_complete', 'Hoàn thành Pomodoro'),
        ('task_create', 'Tạo task mới'),
        ('task_complete', 'Hoàn thành task'),
        ('habit_complete', 'Hoàn thành thói quen'),
        ('flashcard_review', 'Ôn tập flashcard'),
        ('event_create', 'Tạo sự kiện'),
        ('login', 'Đăng nhập'),
        ('settings_update', 'Cập nhật cài đặt'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # Lưu thêm thông tin
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "User Activities"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description="", **metadata):
        """Phương thức tiện ích để log activity"""
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            metadata=metadata
        )

class DailyStats(models.Model):
    """Thống kê hàng ngày của người dùng"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(default=timezone.now)
    
    # Pomodoro
    pomodoro_sessions = models.IntegerField(default=0)
    pomodoro_minutes = models.IntegerField(default=0)
    
    # Tasks
    tasks_created = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    
    # Habits
    habits_completed = models.IntegerField(default=0)
    habits_total = models.IntegerField(default=0)
    
    # Flashcards
    flashcards_reviewed = models.IntegerField(default=0)
    
    # Tính toán
    productivity_score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - Score: {self.productivity_score}"
    
    def calculate_score(self):
        """Tính toán điểm năng suất"""
        score = 0
        
        # Pomodoro: mỗi session = 10 điểm
        score += self.pomodoro_sessions * 10
        
        # Tasks: mỗi task hoàn thành = 15 điểm
        score += self.tasks_completed * 15
        
        # Habits: mỗi habit hoàn thành = 20 điểm
        score += self.habits_completed * 20
        
        # Flashcards: mỗi card = 5 điểm
        score += self.flashcards_reviewed * 5
        
        # Giới hạn tối đa 100 điểm
        self.productivity_score = min(score, 100)
        self.save()
        return self.productivity_score
    
    @classmethod
    def get_or_create_today(cls, user):
        """Lấy hoặc tạo thống kê cho hôm nay"""
        today = timezone.now().date()
        stats, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'pomodoro_sessions': 0,
                'pomodoro_minutes': 0,
                'tasks_created': 0,
                'tasks_completed': 0,
                'habits_completed': 0,
                'habits_total': 0,
                'flashcards_reviewed': 0,
                'productivity_score': 0,
            }
        )
        return stats