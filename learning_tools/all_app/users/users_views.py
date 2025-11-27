from django.shortcuts import render, redirect
from .users_form import *
from .users_models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
import uuid
from django.db import IntegrityError

# Create your views here.
def show_login(request):
    loginForm = login_form()
    context = {
        'form': loginForm,
        'page':'login'
        }
    return render(request,'users/authenticate_page.html',context)

def show_register(request):
    registerForm = register_form()
    context = {
        'form': registerForm,
        'page':'register'
        }
    return render(request,'users/authenticate_page.html',context)

def check_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username, is_deleted=False)
        except User.DoesNotExist:
            return render(request, 'users/authenticate_page.html', {
                'page': 'login',
                'error': 'Tên đăng nhập không tồn tại hoặc đã bị xóa.'
            })

        if check_password(password, user.password):
            # login thủ công
            request.session['user_id'] = user.user_id
            request.session['role'] = user.role
            if user.get_role() == "admin":
                return redirect('admin_manage:admin_home')
            else:
                return redirect('to_do_list:home')
        else:
            return render(request, 'users/authenticate_page.html', {
                'page': 'login',
                'error': 'Mật khẩu không đúng.'
            })

    return redirect('users:login')

def register_user(request):
    if request.method == 'POST':
        form = register_form(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            fullname = form.cleaned_data['fullname']
            password = form.cleaned_data['password']

            try:
                # Kiểm tra username tồn tại
                if User.objects.filter(username=username).exists():
                    return render(request, 'users/authenticate_page.html', {'page': 'register', 'form': form, 'error': 'Tên đăng nhập đã tồn tại'})

                # Kiểm tra email tồn tại
                if User.objects.filter(email=email).exists():
                    return render(request, 'users/authenticate_page.html', {'page': 'register', 'form': form, 'error': 'Email đã tồn tại'})

                # Tạo user mới
                user = User.objects.create(
                    username=username,
                    email=email,
                    password=make_password(password),
                    fullname=fullname,
                    role="user"
                )

                # 2. Tạo các dữ liệu liên quan - KHÔNG cần truyền id
                from all_app.to_do_list.to_do_list_models import ToDoList
                todo = ToDoList.objects.create(user=user)
                
                from all_app.flashcards.flashcards_models import Flashcard  
                flashcard = Flashcard.objects.create(user=user)
                
                from all_app.habit.habit_models import Habit
                habit = Habit.objects.create(user=user)
                
                from all_app.pomodoro.pomodoro_models import Pomodoro
                pomodoro = Pomodoro.objects.create(user=user, title="My Pomodoro")

                from all_app.calendar_app.calendar_models import Calendar
                calendar = Calendar.objects.create(user=user, name="My Calendar")

                request.session['user_id'] = user.user_id
                request.session['role'] = user.role
                return redirect('to_do_list:home')
            except IntegrityError as e:
                # Xử lý nếu username/email bị trùng tại thời điểm lưu (race condition)
                if 'Duplicate entry' in str(e):
                    # Giả định lỗi do trùng username/email
                    # Thường nên kiểm tra chi tiết lỗi DB, nhưng đây là cách đơn giản
                    return render(request, 'users/authenticate_page.html', {'page': 'register', 'form': form, 'error': 'Tên đăng nhập hoặc Email đã tồn tại. Vui lòng thử lại.'})
                else:
                    # Ném lỗi khác nếu không phải lỗi trùng lặp
                    raise
            

        else:
            return render(request, 'users/authenticate_page.html', {'page': 'register', 'form': form, 'error': 'Email đã tồn tại'})
