from all_app.users.users_models import User

class UserMiddleware:
    """
    Middleware để gán user object vào request
    Giúp truy cập user.current_user trong template
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Xử lý trước khi view được gọi
        if 'user_id' in request.session:
            try:
                user_id = request.session['user_id']
                user = User.objects.get(user_id=user_id, is_deleted=False)
                
                # Gán user vào request
                request.user = user
                
                # Gán cho property email_full kiểm tra permission
                user._request_user = user
                
            except User.DoesNotExist:
                # Nếu user không tồn tại, xóa session
                if 'user_id' in request.session:
                    del request.session['user_id']
                if 'role' in request.session:
                    del request.session['role']
                if 'username' in request.session:
                    del request.session['username']
                request.user = None
        else:
            request.user = None
        
        response = self.get_response(request)
        return response


class EmailMaskingMiddleware:
    """
    Middleware để tự động mask email trong context
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Nếu response có context và có user
        if hasattr(response, 'context_data') and response.context_data:
            if 'user' in response.context_data:
                user = response.context_data['user']
                if hasattr(user, 'email_display'):
                    response.context_data['email_masked'] = user.email_display
                    # Chỉ thêm email_full nếu user có quyền
                    if hasattr(user, '_request_user'):
                        response.context_data['email_full'] = user.email_full
        
        return response