# all_app/users/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .users_models import User
from .services import MediaService

class AvatarMiddleware(MiddlewareMixin):
    """Middleware để cập nhật avatar_url trong session"""
    
    def process_request(self, request):
        if 'user_id' in request.session:
            try:
                user = User.objects.get(user_id=request.session['user_id'])
                
                # Chỉ cập nhật nếu chưa có hoặc đã lâu
                if 'avatar_updated' not in request.session:
                    avatar_url = MediaService.get_avatar_url(user)
                    request.session['avatar_url'] = avatar_url
                    request.session['avatar_updated'] = user.updated_at.timestamp()
                    print(f"[AVATAR MIDDLEWARE] Updated session avatar: {avatar_url}")
                
            except User.DoesNotExist:
                # Clear session nếu user không tồn tại
                for key in ['user_id', 'role', 'avatar_url', 'username']:
                    if key in request.session:
                        del request.session[key]
            except Exception as e:
                print(f"[AVATAR MIDDLEWARE] Error: {e}")
        
        return None

# Thêm vào settings.py
# MIDDLEWARE = [
#     # ...
#     'all_app.users.middleware.AvatarMiddleware',
# ]