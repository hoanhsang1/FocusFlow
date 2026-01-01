# all_app/users/context_processors.py
from .users_models import User
from .services import MediaService

def user_context(request):
    """Thêm thông tin user vào context của mọi template"""
    context = {}
    
    if 'user_id' in request.session:
        try:
            user = User.objects.get(user_id=request.session['user_id'])
            context['current_user'] = user  # Dùng current_user để tránh conflict
            
            # Lấy avatar URL
            avatar_url = MediaService.get_avatar_url(user)
            context['avatar_url'] = avatar_url
            
            # Cũng lưu vào session để dùng trong header
            request.session['avatar_url'] = avatar_url
            
            print(f"[CONTEXT PROCESSOR] User: {user.user_id}, Avatar URL: {avatar_url}")
            
        except User.DoesNotExist as e:
            print(f"[CONTEXT PROCESSOR] Error: User not found - {e}")
            # Xóa session
            for key in ['user_id', 'role', 'avatar_url', 'username']:
                if key in request.session:
                    del request.session[key]
        except Exception as e:
            print(f"[CONTEXT PROCESSOR] Error: {e}")
    
    return context