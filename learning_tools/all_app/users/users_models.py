from django.db import models
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]
# ===========================
# USER
# ===========================

class User(models.Model):
    user_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    username = models.CharField(max_length=150, unique=True)
    fullname = models.CharField(max_length=150)
    email = models.CharField(max_length=255, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    role = models.CharField(max_length=10, blank=True, null=True,default='user')

    class Meta:
        db_table = 'User'

    def __str__(self):
        return f"{self.username} ({self.user_id})"
    
    def get_role(self):
        return self.role

class SocialAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='social_accounts')
    provider = models.CharField(max_length=50)  # 'google'
    provider_id = models.CharField(max_length=255)  # Google ID
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'SocialAccount'
        unique_together = ['provider', 'provider_id']
    
    def __str__(self):
        return f"{self.user.username} - {self.provider}"