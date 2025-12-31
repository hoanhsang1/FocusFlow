# all_app/users/services.py - FIXED cho model hiện tại
import os
import uuid
import glob
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from .users_models import MediaFile, User
import traceback

class MediaService:
    """Service quản lý media - PHÙ HỢP với model MediaFile hiện tại"""
    
    @staticmethod
    def upload_avatar(user, image_file):
        """Upload avatar cho user - PHÙ HỢP với model"""
        print(f"\n{'='*60}")
        print(f"[MEDIA SERVICE] Upload avatar for user: {user.user_id}")
        
        try:
            # 1. Tạo thư mục
            avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(avatars_dir, exist_ok=True)
            
            # 2. Mark old avatars as inactive
            ctype = ContentType.objects.get_for_model(User)
            MediaFile.objects.filter(
                content_type=ctype,
                object_id=str(user.user_id),
                file_type='avatar',
                is_active=True
            ).update(is_active=False)
            
            # 3. Tạo tên file mới
            ext = os.path.splitext(image_file.name)[1] or '.jpg'
            filename = f"avatar_{user.user_id}_{uuid.uuid4().hex[:8]}{ext}"
            relative_path = f"avatars/{filename}"
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            
            # 4. Lưu file vật lý
            with open(full_path, 'wb+') as dest:
                for chunk in image_file.chunks():
                    dest.write(chunk)
            
            print(f"[MEDIA SERVICE] File saved: {full_path}")
            
            # 5. Tạo database record - CHỈ DÙNG FIELD CÓ SẴN TRONG MODEL
            media_file = MediaFile.objects.create(
                content_type=ctype,
                object_id=str(user.user_id),
                file=relative_path,  # Đường dẫn tương đối
                file_type='avatar',
                uploaded_by=user,
                is_active=True
            )
            
            print(f"[MEDIA SERVICE] Database record created: ID={media_file.id}")
            print(f"[MEDIA SERVICE] File field: {media_file.file}")
            
            return media_file
            
        except Exception as e:
            print(f"[MEDIA SERVICE] ERROR: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def get_avatar_url(user):
        """Lấy URL avatar của user - FIXED với auto-recovery"""
        print(f"\n[GET AVATAR URL] Called for user: {user.user_id}")
        
        try:
            # 1. Tìm trong database
            ctype = ContentType.objects.get_for_model(User)
            print(f"[GET AVATAR URL] ContentType ID: {ctype.id}")
            
            # Debug: xem tất cả records
            all_avatars = MediaFile.objects.filter(
                content_type=ctype,
                file_type='avatar'
            )
            print(f"[GET AVATAR URL] Total avatar records in DB: {all_avatars.count()}")
            
            for av in all_avatars[:5]:  # Chỉ hiển thị 5 record đầu
                print(f"[GET AVATAR URL]   Record: ID={av.id}, object_id={av.object_id}, active={av.is_active}")
            
            # Tìm active avatar
            avatar = MediaFile.objects.filter(
                content_type=ctype,
                object_id=str(user.user_id),
                file_type='avatar',
                is_active=True
            ).order_by('-uploaded_at').first()
            
            if avatar:
                print(f"[GET AVATAR URL] Found active avatar: ID={avatar.id}")
                print(f"[GET AVATAR URL] File: {avatar.file}")
                
                # Kiểm tra file vật lý
                filepath = os.path.join(settings.MEDIA_ROOT, str(avatar.file))
                if os.path.exists(filepath):
                    print(f"[GET AVATAR URL] Physical file exists: {filepath}")
                    return f"/media/{avatar.file}"
                else:
                    print(f"[GET AVATAR URL] WARNING: Physical file missing")
                    avatar.is_active = False
                    avatar.save()
            
            print(f"[GET AVATAR URL] No active avatar in DB, trying auto-recovery...")
            
            # 2. AUTO-RECOVERY: Tìm file vật lý
            return MediaService._recover_avatar(user)
            
        except Exception as e:
            print(f"[GET AVATAR URL] ERROR: {e}")
            traceback.print_exc()
            return '/static/images/default-avatar.png'
    
    @staticmethod
    def _recover_avatar(user):
        """Tìm file vật lý và tạo database record"""
        print(f"[AUTO-RECOVERY] Looking for files for user {user.user_id}")
        
        avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
        if not os.path.exists(avatars_dir):
            print(f"[AUTO-RECOVERY] Avatars dir not found")
            return '/static/images/default-avatar.png'
        
        # Tìm tất cả file của user này
        pattern = f"*{user.user_id}*"
        matching_files = glob.glob(os.path.join(avatars_dir, pattern))
        
        print(f"[AUTO-RECOVERY] Found {len(matching_files)} matching files")
        
        if not matching_files:
            print(f"[AUTO-RECOVERY] No files found for user")
            return '/static/images/default-avatar.png'
        
        # Lấy file mới nhất
        latest_file = max(matching_files, key=os.path.getmtime)
        filename = os.path.basename(latest_file)
        print(f"[AUTO-RECOVERY] Latest file: {filename}")
        
        try:
            # 1. Đánh dấu tất cả cũ là inactive
            ctype = ContentType.objects.get_for_model(User)
            MediaFile.objects.filter(
                content_type=ctype,
                object_id=str(user.user_id),
                file_type='avatar'
            ).update(is_active=False)
            
            # 2. Tạo record mới - CHỈ DÙNG FIELD CÓ SẴN
            media_file = MediaFile.objects.create(
                content_type=ctype,
                object_id=str(user.user_id),
                file=f"avatars/{filename}",
                file_type='avatar',
                uploaded_by=user,
                is_active=True
            )
            
            print(f"[AUTO-RECOVERY] Created record ID: {media_file.id}")
            return f"/media/avatars/{filename}"
            
        except Exception as e:
            print(f"[AUTO-RECOVERY] Error: {e}")
            return '/static/images/default-avatar.png'