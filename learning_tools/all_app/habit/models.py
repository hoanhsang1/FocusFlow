from django.db import models
import uuid
from django.utils import timezone

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# HABIT MODELS
# ===========================

class Habit(models.Model):
    habit_id = models.CharField(primary_key=True, max_length=10, default=generate_id)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Habit'
        ordering = ['-created_at']

    def __str__(self):
        return f"Habit {self.habit_id} - {self.user.username}"
    
    @property
    def total_lists(self):
        """Tổng số habit lists"""
        return self.habitlist_set.filter(is_deleted=False).count()
    
    @property
    def completed_today(self):
        """Số habit hoàn thành hôm nay"""
        today = timezone.now().date()
        return HabitListLog.objects.filter(
            habitlist__habit=self,
            date=today,
            status='completed',
            is_deleted=False
        ).count()


class HabitList(models.Model):
    habitlist_id = models.CharField(primary_key=True, max_length=10, default=generate_id)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, db_column='habit_id')
    name = models.CharField(max_length=255)
    daily_target = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'HabitList'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} (Target: {self.daily_target})"
    
    def save(self, *args, **kwargs):
        if not self.habitlist_id:
            self.habitlist_id = generate_id()
        super().save(*args, **kwargs)
    
    def soft_delete(self):
        """Soft delete habit list"""
        self.is_deleted = True
        self.save()
    
    @property
    def today_log(self):
        """Lấy log của hôm nay"""
        today = timezone.now().date()
        try:
            return self.habitlistlog_set.get(date=today, is_deleted=False)
        except HabitListLog.DoesNotExist:
            return None
    
    @property
    def today_status(self):
        """Trạng thái hôm nay"""
        log = self.today_log
        return log.status if log else 'not_completed'
    
    @property
    def completion_rate(self):
        """Tỷ lệ hoàn thành (7 ngày gần nhất)"""
        from datetime import timedelta
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        logs = self.habitlistlog_set.filter(
            date__range=[start_date, end_date],
            is_deleted=False
        )
        
        total = logs.count()
        completed = logs.filter(status='completed').count()
        
        return (completed / total * 100) if total > 0 else 0


class HabitListLog(models.Model):
    STATUS_CHOICES = [
        ('not_completed', 'Not Completed'),
        ('completed', 'Completed'),
        ('partially_completed', 'Partially Completed'),
        ('skipped', 'Skipped'),
    ]
    
    log_id = models.CharField(primary_key=True, max_length=10, default=generate_id)
    habitlist = models.ForeignKey(HabitList, on_delete=models.CASCADE, db_column='habitlist_id')
    date = models.DateField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='not_completed')
    pomodoro_history = models.ForeignKey(
        "pomodoro.PomodoroHistory", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        db_column='pomodoro_history_id'
    )
    notes = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'HabitListLog'
        ordering = ['-date']
        unique_together = ['habitlist', 'date']

    def __str__(self):
        return f"{self.habitlist.name} - {self.date} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.log_id:
            self.log_id = generate_id()
        super().save(*args, **kwargs)
    
    def soft_delete(self):
        """Soft delete log"""
        self.is_deleted = True
        self.save()
    
    @property
    def is_today(self):
        """Kiểm tra có phải log của hôm nay không"""
        return self.date == timezone.now().date()
    
    @property
    def day_of_week(self):
        """Ngày trong tuần"""
        return self.date.strftime('%A')
    
    def complete_habit(self, pomodoro_history=None, notes=None):
        """Hoàn thành habit"""
        self.status = 'completed'
        if pomodoro_history:
            self.pomodoro_history = pomodoro_history
        if notes:
            self.notes = notes
        self.save()
    
    def skip_habit(self, notes=None):
        """Bỏ qua habit"""
        self.status = 'skipped'
        if notes:
            self.notes = notes
        self.save()
    
    def partially_complete(self, notes=None):
        """Hoàn thành một phần"""
        self.status = 'partially_completed'
        if notes:
            self.notes = notes
        self.save()