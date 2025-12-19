from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os

class EncryptionService:
    """
    Service mã hóa tập trung cho toàn bộ ứng dụng
    SINGLETON PATTERN - Chỉ có 1 instance duy nhất
    """
    _instance = None  # Biến class để lưu instance duy nhất
    _cipher = None    # Biến class để lưu cipher object
    
    @classmethod
    def get_cipher(cls):
        """
        Lấy cipher object - ĐẢM BẢO CHỈ TẠO 1 LẦN
        """
        if cls._cipher is None:  # Nếu chưa có cipher
            # 1. Ưu tiên lấy key từ environment variable
            key = os.environ.get('ENCRYPTION_KEY')
            
            # 2. Fallback: tạo từ Django secret key
            if not key:
                secret = settings.SECRET_KEY  # Lấy từ Django settings
                # Tạo 32 bytes từ secret key
                # ljust(32): Đảm bảo độ dài 32, nếu ngắn hơn sẽ thêm padding
                # [:32]: Chỉ lấy 32 ký tự đầu (đảm bảo đủ 32 bytes)
                key_bytes = secret.encode().ljust(32)[:32]
                key = base64.urlsafe_b64encode(key_bytes)  # Mã hóa base64
            
            cls._cipher = Fernet(key)  # Tạo Fernet cipher object
        return cls._cipher  # Trả về cipher
    
    @classmethod
    def encrypt(cls, plaintext):
        """Mã hóa plaintext thành ciphertext"""
        if plaintext is None or plaintext == '':
            return plaintext  # Không mã hóa None hoặc empty string
        
        cipher = cls.get_cipher()  # Lấy cipher
        try:
            # Fernet.encrypt() nhận bytes, trả về bytes
            encrypted = cipher.encrypt(plaintext.encode())
            # Mã hóa base64 để lưu vào database dạng text
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            # Nếu lỗi, log nhưng vẫn return plaintext
            # Để app không crash khi có vấn đề mã hóa
            print(f"Encryption error: {e}")
            return plaintext
    
    @classmethod
    def decrypt(cls, ciphertext):
        """Giải mã ciphertext thành plaintext"""
        if ciphertext is None or ciphertext == '':
            return ciphertext
        
        cipher = cls.get_cipher()
        try:
            # Kiểm tra xem có phải dữ liệu đã mã hóa không
            if not cls._is_encrypted(ciphertext):
                return ciphertext  # Nếu không phải, trả về như cũ
            
            # Giải mã base64 → bytes → giải mã Fernet → string
            decrypted = cipher.decrypt(base64.b64decode(ciphertext))
            return decrypted.decode('utf-8')
        except Exception as e:
            # Nếu lỗi giải mã (key sai, data corrupt)
            print(f"Decryption error: {e}")
            return ''  # Trả về empty string thay vì crash
    
    @staticmethod
    def _is_encrypted(text):
        """
        PHÂN BIỆT: plaintext vs ciphertext
        Ciphertext: luôn là base64 string hợp lệ
        """
        try:
            if isinstance(text, str) and len(text) % 4 == 0:
                # Base64 string có độ dài chia hết cho 4
                base64.b64decode(text)  # Thử decode
                return True
        except:
            pass  # Không phải base64
        return False  # Là plaintext
    
    @classmethod
    def hash_password(cls, password):
        """
        HASH password - KHÁC với mã hóa!
        Hash: one-way (không thể giải ngược)
        """
        from django.contrib.auth.hashers import make_password
        return make_password(password)  # Dùng Django built-in
    
    @classmethod
    def verify_password(cls, raw_password, hashed_password):
        """Kiểm tra password"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, hashed_password)