from django.db import models
import uuid
from django.utils import timezone

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# CALENDAR MODELS
# ===========================

class Calendar(models.Model):
    calendar_id = models.CharField(primary_key=True, max_length=10, default=generate_id)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    name = models.CharField(max_length=255, default='Default Calendar')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Calendar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class Event(models.Model):
    event_id = models.CharField(primary_key=True, max_length=10, default=generate_id)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, db_column='calendar_id')
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, null=True, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Event'
        ordering = ['start_at']

    def __str__(self):
        return f"{self.title} - {self.start_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        if not self.event_id:
            self.event_id = generate_id()
        super().save(*args, **kwargs)
    
    def duration_hours(self):
        """Tính thời lượng sự kiện (giờ)"""
        if self.end_at and self.start_at:
            duration = self.end_at - self.start_at
            return duration.total_seconds() / 3600
        return 0
    
    def is_all_day(self):
        """Kiểm tra xem sự kiện có phải cả ngày không"""
        if self.end_at and self.start_at:
            duration = self.end_at - self.start_at
            return duration.days >= 1
        return False
    
    def soft_delete(self):
        """Soft delete event"""
        self.is_deleted = True
        self.save()