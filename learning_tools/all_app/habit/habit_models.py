from django.db import models
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# HABIT TRACKER
# ===========================

class Habit(models.Model):
    habit_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Habit'
        managed = False

    def __str__(self):
        return self.habit_id


class HabitList(models.Model):
    habitlist_id = models.CharField(primary_key=True, max_length=10)
    habit = models.ForeignKey("habit.Habit", on_delete=models.CASCADE, db_column='habit_id')
    name = models.CharField(max_length=255)
    daily_target = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'HabitList'
        managed = False

    def __str__(self):
        return self.name


class HabitListLog(models.Model):
    log_id = models.CharField(primary_key=True, max_length=10)
    habitlist = models.ForeignKey("habit.HabitList", on_delete=models.CASCADE, db_column='habitlist_id')
    date = models.DateField()
    status = models.CharField(max_length=32, default='not_completed')
    pomodoro_history = models.ForeignKey("pomodoro.PomodoroHistory", null=True, blank=True, on_delete=models.SET_NULL, db_column='pomodoro_history_id')
    notes = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'HabitListLog'
        managed = False
        unique_together = ('habitlist', 'date')

    def __str__(self):
        return f"{self.habitlist_id} - {self.date}"
