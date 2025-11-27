from django.db import models
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# TODO LIST
# ===========================

class ToDoList(models.Model):
    todolist_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ToDoList'
        managed = False

    def __str__(self):
        return self.todolist_id


class ToDoListGroup(models.Model):
    group_id = models.CharField(primary_key=True, max_length=10)
    todolist = models.ForeignKey("to_do_list.ToDoList", on_delete=models.CASCADE, db_column='todolist_id')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'ToDoListGroup'
        managed = False

    def __str__(self):
        return self.title


class Task(models.Model):
    task_id = models.CharField(primary_key=True, max_length=10)
    group = models.ForeignKey("to_do_list.ToDoListGroup", on_delete=models.CASCADE, db_column='group_id')
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'Task'
        managed = False

    def __str__(self):
        return self.title
