import os
import django
import sys
import hashlib

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_tools.settings')
django.setup()

from all_app.users.users_models import User, SocialAccount
from core.encryption import EncryptionService

def migrate_existing_data():
    """
    Mã hóa dữ liệu email và provider_id đang là plaintext
    Tạo hash fields cho các bản ghi đã có
    """
    print("🚀 BẮT ĐẦU MIGRATE DỮ LIỆU CŨ")
    print("=" * 50)
    
    # 1. MIGRATE USERS
    print("\n📋 MIGRATING USERS...")
    users = User.objects.all()
    user_count = users.count()
    
    for i, user in enumerate(users, 1):
        try:
            # Kiểm tra xem email đã mã hóa chưa
            if user.email and not EncryptionService._is_encrypted(user.email):
                print(f"  [{i}/{user_count}] User {user.username}: Mã hóa email...")
                
                # Lưu email cũ
                old_email = user.email
                
                # Gán lại để trigger encryption
                user.email = old_email
                
                # Tạo hash fields
                if '@' in old_email:
                    user.email_domain = old_email.split('@')[1]
                
                user.email_hash = hashlib.sha256(old_email.lower().encode()).hexdigest()
                
                # Lưu thay đổi
                user.save(update_fields=['email', 'email_domain', 'email_hash'])
                
                print(f"     ✅ Đã mã hóa: {old_email[:10]}... → {user.email[:20]}...")
            else:
                print(f"  [{i}/{user_count}] User {user.username}: Email đã mã hóa, cập nhật hash...")
                
                # Cập nhật hash cho email đã mã hóa
                if user.email:
                    decrypted_email = EncryptionService.decrypt(user.email)
                    if decrypted_email and '@' in decrypted_email:
                        user.email_domain = decrypted_email.split('@')[1]
                        user.email_hash = hashlib.sha256(decrypted_email.lower().encode()).hexdigest()
                        user.save(update_fields=['email_domain', 'email_hash'])
                        
        except Exception as e:
            print(f"  ❌ Lỗi với user {user.username}: {e}")
    
    # 2. MIGRATE SOCIAL ACCOUNTS
    print("\n📋 MIGRATING SOCIAL ACCOUNTS...")
    social_accounts = SocialAccount.objects.all()
    social_count = social_accounts.count()
    
    for i, social in enumerate(social_accounts, 1):
        try:
            # Mã hóa email nếu cần
            if social.email and not EncryptionService._is_encrypted(social.email):
                print(f"  [{i}/{social_count}] Social {social.provider}: Mã hóa email...")
                old_email = social.email
                social.email = old_email
            
            # Mã hóa provider_id nếu cần
            if social.provider_id and not EncryptionService._is_encrypted(social.provider_id):
                print(f"  [{i}/{social_count}] Social {social.provider}: Mã hóa provider_id...")
                old_provider_id = social.provider_id
                social.provider_id = old_provider_id
            
            # Tạo hash fields
            if social.provider_id:
                provider_id_decrypted = EncryptionService.decrypt(social.provider_id) if social.provider_id else ''
                social.provider_id_hash = hashlib.sha256(
                    f"{social.provider}:{provider_id_decrypted}".encode()
                ).hexdigest()
            
            if social.email:
                email_decrypted = EncryptionService.decrypt(social.email) if social.email else ''
                social.email_hash = hashlib.sha256(email_decrypted.lower().encode()).hexdigest()
            
            # Lưu tất cả thay đổi
            social.save()
            print(f"     ✅ Đã cập nhật social account")
            
        except Exception as e:
            print(f"  ❌ Lỗi với social account {social.id}: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 MIGRATION HOÀN TẤT!")
    print(f"✅ Đã xử lý: {user_count} users, {social_count} social accounts")

if __name__ == "__main__":
    migrate_existing_data()