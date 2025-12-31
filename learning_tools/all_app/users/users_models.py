from django.db import models
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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
    

class MediaFile(models.Model):
    """Model quản lý file upload"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=10)  # Vì user_id là CharField
    content_object = GenericForeignKey('content_type', 'object_id')
    
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField(max_length=20)  # 'avatar', 'product', etc
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, to_field='user_id')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'MediaFile'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.file_type} - {self.file.name}"