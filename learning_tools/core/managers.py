from django.db import models
import hashlib
from core.encryption import EncryptionService

class EncryptedUserManager(models.Manager):
    """
    CUSTOM MANAGER cho User model
    Manager: Class quản lý database queries
    """
    
    def create_user(self, username, email, password, **extra_fields):
        """
        Tạo user với mã hóa tự động
        Thay thế cho User.objects.create()
        """
        user = self.model(username=username, **extra_fields)  # Tạo instance
        user.email = email  # Tự động mã hóa qua field
        user.set_password(password)  # Hash password
        user.save()
        return user
    
    def get_by_email(self, email):
        """
        TÌM USER BẰNG EMAIL (mà không giải mã)
        Sử dụng email_hash thay vì email trực tiếp
        """
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
        return self.filter(email_hash=email_hash).first()
        # SQL: SELECT * FROM User WHERE email_hash = 'hash_value'
    
    def search_by_email_domain(self, domain):
        """Tìm user theo domain email"""
        return self.filter(email_domain__icontains=domain)
        # SQL: SELECT * FROM User WHERE email_domain LIKE '%domain%'


class SocialAccountManager(models.Manager):
    
    def get_by_provider_id(self, provider, provider_id):
        """
        Tìm social account bằng provider_id đã mã hóa
        """
        # Tạo hash giống như trong save() method
        provider_id_hash = hashlib.sha256(
            f"{provider}:{provider_id}".encode()
        ).hexdigest()
        
        return self.filter(
            provider=provider,
            provider_id_hash=provider_id_hash
        ).first()