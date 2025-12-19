from django.shortcuts import render, redirect
from .users_form import *
from .users_models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
import uuid
from django.db import IntegrityError
import requests
from django.conf import settings
from django.contrib import messages
import hashlib
from core.encryption import EncryptionService

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
    """
    ĐĂNG NHẬP VỚI MÃ HÓA
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # 1. Tìm user bằng username (không mã hóa)
            user = User.objects.get(username=username, is_deleted=False)
        except User.DoesNotExist:
            return render(request, 'users/authenticate_page.html', {
                'page': 'login',
                'error': 'Tên đăng nhập không tồn tại hoặc đã bị xóa.'
            })

        # 2. Kiểm tra password bằng method check_password() của model
        if user.check_password(password):
            # login thủ công
            request.session['user_id'] = user.user_id
            request.session['role'] = user.role
            request.session['username'] = user.username
            
            # Gán user vào session để property email_full hoạt động
            request.session['_user_obj_id'] = user.user_id
            
            if user.get_role() == "admin":
                return redirect('admin_manage:admin_manage_dashboard')
            else:
                return redirect('to_do_list:home')
        else:
            return render(request, 'users/authenticate_page.html', {
                'form': login_form(),
                'page': 'login',
                'error': 'Mật khẩu không đúng.'
            })

    return redirect('users:login')

def register_user(request):
    """
    ĐĂNG KÝ VỚI MÃ HÓA
    """
    if request.method == 'POST':
        form = register_form(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email'].lower()  # Chuyển lowercase
            fullname = form.cleaned_data['fullname']
            password = form.cleaned_data['password']

            try:
                # 1. Kiểm tra username tồn tại
                if User.objects.filter(username=username).exists():
                    return render(request, 'users/authenticate_page.html', {
                        'page': 'register', 
                        'form': form, 
                        'error': 'Tên đăng nhập đã tồn tại'
                    })

                # 2. Kiểm tra email tồn tại bằng HASH
                email_hash = hashlib.sha256(email.encode()).hexdigest()
                if User.objects.filter(email_hash=email_hash).exists():
                    return render(request, 'users/authenticate_page.html', {
                        'page': 'register', 
                        'form': form, 
                        'error': 'Email đã tồn tại'
                    })

                # 3. Tạo user mới với UserManager (tự động mã hóa email)
                user = User.objects.create(
                    username=username,
                    email=email,  # Sẽ tự động mã hóa trong field
                    password=password,
                    fullname=fullname,
                    role="user"
                )
                print(f"✅ User created: {user.user_id}")

                # 4. Tạo các dữ liệu liên quan
                try:
                    from all_app.to_do_list.to_do_list_models import ToDoList
                    todo = ToDoList.objects.create(user=user)
                    print(f"✅ ToDoList created: {todo.todolist_id}")
                    
                    from all_app.flashcards.flashcards_models import Flashcard  
                    flashcard = Flashcard.objects.create(user=user)
                    print(f"✅ Flashcard created: {flashcard.flashcard_id}")
                    
                    from all_app.habit.habit_models import Habit
                    habit = Habit.objects.create(user=user)
                    print(f"✅ Habit created: {habit.habit_id}")
                    
                    from all_app.pomodoro.pomodoro_models import Pomodoro
                    pomodoro = Pomodoro.objects.create(user=user, title="My Pomodoro")
                    print(f"✅ Pomodoro created: {pomodoro.pomodoro_id}")
                    
                    from all_app.calendar_app.calendar_models import Calendar
                    calendar = Calendar.objects.create(user=user, name="My Calendar")
                    print(f"✅ Calendar created: {calendar.calendar_id}")
                    
                except Exception as model_error:
                    print(f"❌ Failed to create related data: {model_error}")
                    import traceback
                    traceback.print_exc()
                    # Xóa user nếu tạo dữ liệu thất bại
                    user.delete()
                    return render(request, 'users/authenticate_page.html', {
                        'page': 'register', 
                        'form': form, 
                        'error': 'Không thể thiết lập tài khoản. Vui lòng thử lại.'
                    })

                # 5. Đăng nhập user
                request.session['user_id'] = user.user_id
                request.session['role'] = user.role
                request.session['username'] = user.username
                request.session['_user_obj_id'] = user.user_id
                
                messages.success(request, f"Đăng ký thành công! Chào mừng {fullname}")
                return redirect('to_do_list:home')
                
            except IntegrityError as e:
                print(f"❌ IntegrityError: {e}")
                if 'Duplicate entry' in str(e):
                    return render(request, 'users/authenticate_page.html', {
                        'page': 'register', 
                        'form': form, 
                        'error': 'Tên đăng nhập hoặc Email đã tồn tại. Vui lòng thử lại.'
                    })
                else:
                    raise
            

        else:
            # Form không hợp lệ
            return render(request, 'users/authenticate_page.html', {
                'page': 'register', 
                'form': form, 
                'error': 'Vui lòng kiểm tra lại thông tin nhập'
            })


def google_login(request):
    """Redirect đến Google OAuth page"""
    # Các tham số Google OAuth
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'prompt': 'select_account',
    }
    print(f"[DEBUG] Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    
    # Tạo Google OAuth URL
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    return redirect(auth_url)

def google_callback(request):
    """
    XỬ LÝ GOOGLE CALLBACK VỚI MÃ HÓA
    """
    # Lấy authorization code từ Google
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f"Lỗi đăng nhập Google: {error}")
        return redirect('users:login_form')
    
    if not code:
        messages.error(request, "Không nhận được mã xác thực từ Google")
        return redirect('users:login_form')
    
    try:
        print(f"[GOOGLE] Received code: {code[:20]}...")
        
        # 1. Đổi code lấy access token
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data, timeout=10)
        
        if token_response.status_code != 200:
            print(f"[GOOGLE] Token error: {token_response.text}")
            messages.error(request, "Không thể lấy token từ Google")
            return redirect('users:login_form')
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        # 2. Lấy thông tin user từ Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if user_info_response.status_code != 200:
            print(f"[GOOGLE] User info error: {user_info_response.text}")
            messages.error(request, "Không thể lấy thông tin từ Google")
            return redirect('users:login_form')
        
        user_info = user_info_response.json()
        print(f"[GOOGLE] User info: {user_info}")
        
        # 3. Xử lý thông tin user
        google_id = user_info.get('sub')  # Google user ID
        email = user_info.get('email', '').lower()  # Luôn lowercase
        name = user_info.get('name', '')
        
        if not email:
            messages.error(request, "Google không cung cấp email")
            return redirect('users:login_form')
        
        print(f"[GOOGLE] Processing: {email}, google_id: {google_id}")
        
        # 4. Tìm social account bằng provider_id_hash
        # Tạo hash từ provider_id để tìm
        provider_id_hash = hashlib.sha256(
            f"google:{google_id}".encode()
        ).hexdigest()
        
        try:
            # Sử dụng SocialAccountManager để tìm
            social_account = SocialAccount.objects.get_by_provider_id(
                provider='google', 
                provider_id=google_id
            )
            user = social_account.user
            print(f"[GOOGLE] Found existing social account for: {user.username}")
            
        except SocialAccount.DoesNotExist:
            print(f"[GOOGLE] No social account found, checking email...")
            
            # 5. Tìm user bằng email_hash
            email_hash = hashlib.sha256(email.encode()).hexdigest()
            try:
                user = User.objects.get(email_hash=email_hash)
                print(f"[GOOGLE] Found existing user by email: {user.username}")
                
                # Tạo liên kết Google với tài khoản hiện có
                # Sử dụng SocialAccount.objects.create (sẽ tự động mã hóa)
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    provider_id=google_id,  # Tự động mã hóa
                    email=email              # Tự động mã hóa
                )
                messages.info(request, "Đã liên kết tài khoản Google với tài khoản hiện có")
                
            except User.DoesNotExist:
                print(f"[GOOGLE] Creating new user...")
                
                # 6. Tạo user mới
                # Tạo username từ email
                username_base = email.split('@')[0]
                username = username_base
                counter = 1
                
                # Đảm bảo username là unique
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1
                
                print(f"[GOOGLE] Creating user: {username}")
                
                # Tạo user với UserManager (tự động mã hóa email)
                user = User.objects.create(
                    username=username,
                    email=email,  # Tự động mã hóa
                    password=User.objects.make_random_password(),
                    fullname=name,
                    role="user"
                )
                print(f"[GOOGLE] User created: {user.user_id}")
                
                try:
                    # Tạo dữ liệu liên quan
                    print(f"[GOOGLE] Creating related data...")
                    from all_app.to_do_list.to_do_list_models import ToDoList
                    ToDoList.objects.create(user=user)
                    
                    from all_app.flashcards.flashcards_models import Flashcard  
                    Flashcard.objects.create(user=user)
                    
                    from all_app.habit.habit_models import Habit
                    Habit.objects.create(user=user)
                    
                    from all_app.pomodoro.pomodoro_models import Pomodoro
                    Pomodoro.objects.create(user=user, title="My Pomodoro")
                    
                    from all_app.calendar_app.calendar_models import Calendar
                    Calendar.objects.create(user=user, name="My Calendar")
                    
                    print(f"[GOOGLE] Related data created")
                    
                except Exception as model_error:
                    print(f"[GOOGLE ERROR] Failed to create related data: {model_error}")
                    user.delete()
                    messages.error(request, "Không thể thiết lập tài khoản. Vui lòng thử lại.")
                    return redirect('users:login_form')
                
                # Tạo social account (tự động mã hóa)
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    provider_id=google_id,
                    email=email
                )
                print(f"[GOOGLE] Social account created")
                
                messages.success(request, "Đã tạo tài khoản mới với Google")

        # 7. Đăng nhập user
        print(f"[GOOGLE] Setting session for user: {user.user_id}")
        request.session['user_id'] = str(user.user_id)
        request.session['role'] = user.role
        request.session['username'] = user.username
        request.session['_user_obj_id'] = user.user_id
        
        messages.success(request, f"Đăng nhập thành công với {user.email_display}")
        
        # 8. Redirect về trang chủ
        if user.role == "admin":
            return redirect('admin_manage:admin_manage_dashboard')
        else:
            return redirect('to_do_list:home')
            
    except requests.Timeout:
        print(f"[GOOGLE] Request timeout")
        messages.error(request, "Kết nối với Google quá thời gian chờ")
        return redirect('users:login_form')
    except requests.RequestException as e:
        print(f"[GOOGLE] Request error: {e}")
        messages.error(request, f"Lỗi kết nối: {str(e)}")
        return redirect('users:login_form')
    except Exception as e:
        print(f"[GOOGLE] General error: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Lỗi hệ thống: {str(e)}")
        return redirect('users:login_form')


def logout_user(request):
    """
    ĐĂNG XUẤT
    """
    # Xóa tất cả session
    request.session.flush()
    messages.success(request, "Đã đăng xuất thành công")
    return redirect('users:login_form')


def user_profile(request):
    """
    XEM THÔNG TIN USER
    """
    if 'user_id' not in request.session:
        return redirect('users:login_form')
    
    try:
        user_id = request.session['user_id']
        user = User.objects.get(user_id=user_id, is_deleted=False)
        
        # Gán request user để property email_full kiểm tra permission
        user._request_user = user
        
        context = {
            'user': user,
            'email_display': user.email_display,
            'email_full': user.email_full,  # Sẽ hiển thị full email vì là chính user
        }
        
        return render(request, 'users/profile.html', context)
        
    except User.DoesNotExist:
        messages.error(request, "Người dùng không tồn tại")
        return redirect('users:login_form')


def update_profile(request):
    """
    CẬP NHẬT THÔNG TIN USER
    """
    if 'user_id' not in request.session:
        return redirect('users:login_form')
    
    if request.method == 'POST':
        try:
            user_id = request.session['user_id']
            user = User.objects.get(user_id=user_id, is_deleted=False)
            
            # Cập nhật thông tin
            fullname = request.POST.get('fullname')
            new_email = request.POST.get('email', '').lower()
            
            if fullname:
                user.fullname = fullname
            
            # Nếu thay đổi email
            if new_email and new_email != user.email:
                # Kiểm tra email mới có tồn tại không
                new_email_hash = hashlib.sha256(new_email.encode()).hexdigest()
                if User.objects.filter(email_hash=new_email_hash).exclude(user_id=user_id).exists():
                    messages.error(request, "Email mới đã được sử dụng")
                else:
                    user.email = new_email  # Tự động mã hóa
            
            user.save()
            messages.success(request, "Cập nhật thông tin thành công")
            
        except Exception as e:
            print(f"❌ Update error: {e}")
            messages.error(request, f"Cập nhật thất bại: {str(e)}")
    
    return redirect('users:profile')


def change_password(request):
    """
    THAY ĐỔI MẬT KHẨU
    """
    if 'user_id' not in request.session:
        return redirect('users:login_form')
    
    if request.method == 'POST':
        try:
            user_id = request.session['user_id']
            user = User.objects.get(user_id=user_id, is_deleted=False)
            
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Kiểm tra mật khẩu hiện tại
            if not user.check_password(current_password):
                messages.error(request, "Mật khẩu hiện tại không đúng")
                return redirect('users:profile')
            
            # Kiểm tra mật khẩu mới
            if new_password != confirm_password:
                messages.error(request, "Mật khẩu mới không khớp")
                return redirect('users:profile')
            
            if len(new_password) < 6:
                messages.error(request, "Mật khẩu phải có ít nhất 6 ký tự")
                return redirect('users:profile')
            
            # Cập nhật mật khẩu
            user.set_password(new_password)
            user.save()
            
            messages.success(request, "Thay đổi mật khẩu thành công")
            
        except Exception as e:
            print(f"❌ Change password error: {e}")
            messages.error(request, f"Thay đổi mật khẩu thất bại: {str(e)}")
    
    return redirect('users:profile')