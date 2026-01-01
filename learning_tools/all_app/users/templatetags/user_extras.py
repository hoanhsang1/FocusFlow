# all_app/users/templatetags/user_extras.py
from django import template
from django.templatetags.static import static
from ..users_models import User
from ..services import MediaService

register = template.Library()

@register.simple_tag
def get_default_avatar_url():
    """Template tag để lấy default avatar URL"""
    return static('images/default-avatar.png')

@register.simple_tag(takes_context=True)
def get_user_info(context):
    """Lấy thông tin user hiện tại"""
    request = context.get('request')
    if not request:
        return None
    
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    
    try:
        return User.objects.get(user_id=user_id, is_deleted=False)
    except User.DoesNotExist:
        return None

@register.simple_tag(takes_context=True)
def get_user_avatar_url(context):
    """Lấy avatar URL thật của user hiện tại"""
    request = context.get('request')
    if not request:
        return static('images/default-avatar.png')
    
    user_id = request.session.get('user_id')
    if not user_id:
        return static('images/default-avatar.png')
    
    try:
        user = User.objects.get(user_id=user_id, is_deleted=False)
        avatar_url = MediaService.get_avatar_url(user)
        
        # Debug
        print(f"[TEMPLATE TAG] User: {user.user_id}, Avatar URL: {avatar_url}")
        
        return avatar_url or static('images/default-avatar.png')
    except Exception as e:
        print(f"[TEMPLATE TAG] Error: {e}")
        return static('images/default-avatar.png')