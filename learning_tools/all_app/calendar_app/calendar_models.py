from django.db import models
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# CALENDAR
# ===========================

class Calendar(models.Model):
    calendar_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    name = models.CharField(max_length=255, default='Default Calendar')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Calendar'
        managed = False

    def __str__(self):
        return self.name


class Event(models.Model):
    event_id = models.CharField(primary_key=True, max_length=10)
    calendar = models.ForeignKey("calendar_app.Calendar", on_delete=models.CASCADE, db_column='calendar_id')
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, null=True, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Event'
        managed = False

    def __str__(self):
        return self.title
