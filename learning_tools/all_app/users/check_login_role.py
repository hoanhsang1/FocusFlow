from django.shortcuts import render, redirect
from django.http import HttpResponse

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('users:login_form')

            user_role = request.session.get('role')

            
            if user_role != allowed_roles:
                return HttpResponse("Không có quyền truy cập.", status=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def check_login(view_func):
        def wrapper(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('users:login_form')

            return view_func(request, *args, **kwargs)
        return wrapper