# all_app/users/check_login_role.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from functools import wraps

def check_login(view_func):
    """
    Decorator kiểm tra đăng nhập - SỬ DỤNG DJANGO AUTH THAY VÌ SESSION
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Cách 1: Kiểm tra session (của bạn)
        if 'user_id' not in request.session:
            return redirect('users:login_form')
        
        # Cách 2: Kiểm tra Django auth (tốt hơn)
        if not request.user.is_authenticated:
            return redirect('users:login_form')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(allowed_roles):
    """
    Decorator kiểm tra role - ĐÃ SỬA LỖI
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # QUAN TRỌNG: Kiểm tra đăng nhập TRƯỚC
            if not request.user.is_authenticated:
                return redirect('users:login_form')
            
            # Lấy user_id từ session (của bạn)
            user_id = request.session.get('user_id')
            if not user_id:
                return redirect('users:login_form')
            
            # Lấy role từ session (của bạn)
            user_role = request.session.get('role', 'user')
            
            # Kiểm tra role
            if user_role != allowed_roles:
                return HttpResponse("Không có quyền truy cập.", status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Decorator mới - AN TOÀN HƠN
def auth_required(view_func):
    """
    Decorator kết hợp cả auth và role check
    Sử dụng: @auth_required hoặc @auth_required(role='admin')
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Kiểm tra Django auth
        if not request.user.is_authenticated:
            return redirect('users:login_form')
        
        # Kiểm tra session (nếu cần)
        if 'user_id' not in request.session:
            return redirect('users:login_form')
        
        return view_func(request, *args, **kwargs)
    return wrapper