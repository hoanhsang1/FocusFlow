import hashlib
from django.db.models import Q
from .models import User

def find_user_by_email_or_username(identifier):
    """
    Tìm user bằng email hoặc username
    identifier: email hoặc username (plaintext)
    """
    # Tìm bằng username (không mã hóa)
    try:
        return User.objects.get(username=identifier, is_deleted=False)
    except User.DoesNotExist:
        pass
    
    # Tìm bằng email hash
    email_hash = hashlib.sha256(identifier.lower().encode()).hexdigest()
    try:
        return User.objects.get(email_hash=email_hash, is_deleted=False)
    except User.DoesNotExist:
        pass
    
    return None


def get_user_safe_info(user):
    """
    Trả về thông tin an toàn của user để hiển thị
    """
    return {
        'user_id': user.user_id,
        'username': user.username,
        'fullname': user.fullname,
        'email_display': user.email_display,
        'role': user.role,
        'created_at': user.created_at,
    }


def mask_email_for_display(email):
    """
    Mask email để hiển thị an toàn
    """
    if not email:
        return ""
    
    if '@' in email:
        parts = email.split('@')
        if len(parts[0]) > 2:
            masked = parts[0][0] + '***' + parts[0][-1]
        else:
            masked = '***'
        return f"{masked}@{parts[1]}"
    
    return "***@***"