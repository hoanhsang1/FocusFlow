from all_app.users.users_models import User

def user_context(request):
    """
    Thêm user object vào mọi template context
    """
    context = {}
    
    if hasattr(request, 'user') and request.user:
        context['current_user'] = request.user
        
        # Thêm email hiển thị
        if hasattr(request.user, 'email_display'):
            context['user_email_display'] = request.user.email_display
        
        # Thêm email full nếu có quyền
        if hasattr(request.user, 'email_full'):
            context['user_email_full'] = request.user.email_full
    
    return context