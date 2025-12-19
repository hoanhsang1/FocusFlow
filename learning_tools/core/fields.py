from django.db import models
from .encryption import EncryptionService

class EncryptedEmailField(models.EmailField):
    """
    KẾ THỪA từ Django's EmailField
    OVERRIDE 3 phương thức quan trọng:
    1. from_db_value(): Khi lấy từ DB → giải mã
    2. get_prep_value(): Trước khi lưu DB → mã hóa
    3. to_python(): Khi Python truy cập → giải mã
    """
    
    def from_db_value(self, value, expression, connection):
        """
        ĐƯỢC GỌI KHI: Django lấy giá trị từ database
        MỤC ĐÍCH: Chuyển database value → Python value
        """
        if value is None:
            return value
        return EncryptionService.decrypt(value)  # Giải mã
    
    def get_prep_value(self, value):
        """
        ĐƯỢC GỌI KHI: Django chuẩn bị lưu vào database
        MỤC ĐÍCH: Chuyển Python value → database value
        """
        if value is None:
            return None
        return EncryptionService.encrypt(value)  # Mã hóa
    
    def to_python(self, value):
        """
        ĐƯỢC GỌI KHI: Truy cập giá trị từ Python object
        Ví dụ: user.email (truy cập attribute)
        """
        if isinstance(value, str):
            # Nếu đã là string (từ form input)
            return value
        if value is None:
            return value
        return EncryptionService.decrypt(value)


class EncryptedCharField(models.CharField):
    """Tương tự cho CharField"""
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return EncryptionService.decrypt(value)
    
    def get_prep_value(self, value):
        if value is None:
            return None
        return EncryptionService.encrypt(str(value))  # Đảm bảo là string
    
    def to_python(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return value
        return EncryptionService.decrypt(value)