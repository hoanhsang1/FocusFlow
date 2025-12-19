from django.db import models
import uuid
from core.fields import EncryptedEmailField, EncryptedCharField
from core.encryption import EncryptionService

def generate_id():
    """Hàm tạo ID ngắn từ UUID"""
    return str(uuid.uuid4())[:10]  # Lấy 10 ký tự đầu của UUID

class User(models.Model):
    # Primary key tự động
    user_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    
    # Thông tin công khai - KHÔNG mã hóa
    username = models.CharField(max_length=150, unique=True)
    fullname = models.CharField(max_length=150)
    
    # EMAIL: DÙNG ENCRYPTED FIELD
    email = EncryptedEmailField(max_length=255, unique=True, null=True, blank=True)
    # Khi gán: user.email = "test@example.com" → tự động mã hóa
    # Khi đọc: print(user.email) → tự động giải mã
    
    # PASSWORD: Hash thông thường
    password = models.CharField(max_length=255)
    
    # SEARCH FIELDS - không mã hóa, dùng để tìm kiếm
    email_domain = models.CharField(max_length=100, editable=False, blank=True, null=True)
    email_hash = models.CharField(max_length=64, editable=False, blank=True, null=True)
    # editable=False: Không hiển thị trong Django Admin
    
    # Meta fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    role = models.CharField(max_length=10, blank=True, null=True, default='user')

    class Meta:
        db_table = 'User'  # Tên table trong database

    def __str__(self):
        return f"{self.username} ({self.user_id})"
    
    def get_role(self):
        return self.role
    
    def set_password(self, raw_password):
        """Hash password thay vì lưu plaintext"""
        self.password = EncryptionService.hash_password(raw_password)
    
    def check_password(self, raw_password):
        """Kiểm tra password hash"""
        return EncryptionService.verify_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        """
        OVERRIDE save() để thêm logic trước khi lưu
        Được gọi TRƯỚC khi lưu vào database
        """
        
        # 1. TẠO EMAIL DOMAIN để search
        if self.email:
            # Kiểm tra xem email đã mã hóa chưa
            if EncryptionService._is_encrypted(self.email):
                # Nếu đã mã hóa → giải mã
                decrypted_email = EncryptionService.decrypt(self.email)
            else:
                # Nếu chưa mã hóa (lần đầu save)
                decrypted_email = self.email
            
            # Tách domain từ email: test@example.com → example.com
            if '@' in decrypted_email:
                self.email_domain = decrypted_email.split('@')[1]
            
            # 2. TẠO EMAIL HASH để tìm kiếm mà không giải mã
            import hashlib
            # SHA256 hash của email lowercase
            self.email_hash = hashlib.sha256(
                decrypted_email.lower().encode()
            ).hexdigest()
            # Hash là one-way, không thể lấy lại email gốc
        
        # 3. HASH PASSWORD nếu là plaintext
        if self.password and not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$')):
            # Kiểm tra format hash
            self.password = EncryptionService.hash_password(self.password)
        
        # Gọi save() của parent class
        super().save(*args, **kwargs)
    
    @property
    def email_display(self):
        """
        PROPERTY: Trả về email đã mask để hiển thị an toàn
        Property: Giống method nhưng gọi như attribute
        Ví dụ: user.email_display (không cần dấu ngoặc)
        """
        if not self.email:
            return ""
        
        try:
            # Giải mã email
            decrypted = EncryptionService.decrypt(self.email)
            if '@' in decrypted:
                parts = decrypted.split('@')
                if len(parts[0]) > 2:
                    # Mask phần local: john → j***n
                    masked = parts[0][0] + '***' + parts[0][-1]
                else:
                    masked = '***'
                return f"{masked}@{parts[1]}"  # j***n@example.com
            return decrypted
        except:
            return "***@***"  # Fallback
    
    @property
    def email_full(self):
        """
        Property chỉ trả về email đầy đủ nếu có quyền
        Cần gán: user._request_user = request.user trước
        """
        if hasattr(self, '_request_user'):
            # Kiểm tra permission
            if self._request_user.role == 'admin' or self._request_user.pk == self.pk:
                return EncryptionService.decrypt(self.email)
        # Nếu không có quyền → trả về masked version
        return self.email_display
    
class SocialAccount(models.Model):
    # Primary key là UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ForeignKey đến User
    user = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE,  # Khi user bị xóa → social account cũng bị xóa
        related_name='social_accounts'  # user.social_accounts.all()
    )
    
    provider = models.CharField(max_length=50)  # 'google', 'facebook'
    
    # MÃ HÓA provider_id (Google ID, Facebook ID)
    provider_id = EncryptedCharField(max_length=255)
    
    # MÃ HÓA email
    email = EncryptedEmailField()
    
    # SEARCH FIELDS - dùng hashes
    provider_id_hash = models.CharField(max_length=64, editable=False, blank=True, null=True)
    email_hash = models.CharField(max_length=64, editable=False, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Unique constraint trên provider + provider_id_hash
        unique_together = ['provider', 'provider_id_hash']
        db_table = 'social_account'
    
    def __str__(self):
        return f"{self.user.username} - {self.provider}"
    
    def save(self, *args, **kwargs):
        """Logic trước khi lưu"""
        if self.provider_id:
            import hashlib
            # Giải mã provider_id nếu cần
            provider_id_decrypted = EncryptionService.decrypt(
                self.provider_id
            ) if self.provider_id else ''
            
            # Tạo hash từ: "google:123456789"
            # Đảm bảo unique cho từng provider
            self.provider_id_hash = hashlib.sha256(
                f"{self.provider}:{provider_id_decrypted}".encode()
            ).hexdigest()
        
        if self.email:
            # Tạo email hash
            email_decrypted = EncryptionService.decrypt(self.email)
            self.email_hash = hashlib.sha256(
                email_decrypted.lower().encode()
            ).hexdigest()
        
        super().save(*args, **kwargs)