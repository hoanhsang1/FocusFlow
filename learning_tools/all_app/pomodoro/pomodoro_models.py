from django.db import models
import uuid

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
        ('running', 'running'),
        ('paused', 'paused'),
        ('stopped', 'stopped'),
        ('completed', 'completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='stopped')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Pomodoro'
        managed = False

    def __str__(self):
        return f"{self.title} ({self.pomodoro_id})"


class PomodoroHistory(models.Model):
    history_id = models.CharField(primary_key=True, max_length=10)
    pomodoro = models.ForeignKey("pomodoro.Pomodoro", null=True, blank=True, on_delete=models.SET_NULL, db_column='pomodoro_id')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField()
    study_topic = models.CharField(max_length=255, null=True, blank=True)

    STATUS_CHOICES = [
        ('completed', 'completed'),
        ('interrupted', 'interrupted')
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='completed')

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'PomodoroHistory'
        managed = False

    def __str__(self):
        return self.history_id
