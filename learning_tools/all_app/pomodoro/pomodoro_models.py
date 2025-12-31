from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# POMODORO
# ===========================

class Pomodoro(models.Model):
    pomodoro_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    title = models.CharField(max_length=255, default='Default Pomodoro')

    STATUS_CHOICES = [
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('stopped', 'Stopped'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='stopped')
    
    # Thêm fields mới cho tính năng Pomodoro
    work_duration = models.IntegerField(default=25)  # phút
    break_duration = models.IntegerField(default=5)   # phút
    current_session = models.CharField(max_length=10, default='work')  # 'work' or 'break'
    sessions_completed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Pomodoro'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def get_current_duration(self):
        """Lấy thời lượng hiện tại dựa trên session type"""
        if self.current_session == 'work':
            return self.work_duration
        return self.break_duration
    
    def start_timer(self):
        """Bắt đầu Pomodoro timer"""
        self.status = 'running'
        self.save()
        
        # Tạo history record
        PomodoroHistory.objects.create(
            pomodoro=self,
            start_time=timezone.now(),
            study_topic=f"{self.title} - {self.current_session} session",
            status='running'  # Tạm thời là running, sẽ update khi kết thúc
        )
    
    def pause_timer(self):
        """Tạm dừng Pomodoro"""
        self.status = 'paused'
        self.save()
    
    def stop_timer(self):
        """Dừng Pomodoro"""
        self.status = 'stopped'
        self.save()
        
        # Cập nhật history record
        history = PomodoroHistory.objects.filter(
            pomodoro=self,
            end_time__isnull=True
        ).order_by('-start_time').first()
        
        if history:
            history.end_time = timezone.now()
            duration = (history.end_time - history.start_time).total_seconds() / 60
            history.duration_minutes = int(duration)
            history.status = 'completed' if duration >= 1 else 'interrupted'
            history.save()
    
    def complete_session(self):
        """Hoàn thành một session"""
        if self.current_session == 'work':
            self.sessions_completed += 1
            self.current_session = 'break'
        else:
            self.current_session = 'work'
        
        self.save()


class PomodoroHistory(models.Model):
    history_id = models.CharField(primary_key=True, max_length=10)
    pomodoro = models.ForeignKey("pomodoro.Pomodoro", null=True, blank=True, 
                                on_delete=models.SET_NULL, db_column='pomodoro_id')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    study_topic = models.CharField(max_length=255, null=True, blank=True)

    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('interrupted', 'Interrupted')
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='running')

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'PomodoroHistory'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.history_id} - {self.study_topic or 'No topic'}"
    
    def save(self, *args, **kwargs):
        """Tự động tạo history_id nếu chưa có"""
        if not self.history_id:
            self.history_id = generate_id()
        super().save(*args, **kwargs)
    
    def get_duration_display(self):
        """Hiển thị thời lượng đẹp"""
        if self.duration_minutes:
            hours = self.duration_minutes // 60
            minutes = self.duration_minutes % 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "N/A"
    
    def soft_delete(self):
        """Soft delete history"""
        self.is_deleted = True
        self.save()


class PomodoroSettings(models.Model):
    """
    Model mới: Lưu cài đặt Pomodoro của user
    """
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, db_column='user_id')
    
    # Cài đặt thời gian
    default_work_duration = models.IntegerField(default=25)
    default_break_duration = models.IntegerField(default=5)
    auto_start_break = models.BooleanField(default=True)
    
    # Cài đặt âm thanh/thông báo
    enable_sounds = models.BooleanField(default=True)
    enable_notifications = models.BooleanField(default=True)
    
    # Cài đặt hiển thị
    theme = models.CharField(max_length=50, default='default')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'PomodoroSettings'

    def __str__(self):
        return f"Settings for {self.user.username}"