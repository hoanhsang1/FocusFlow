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
                return redirect('admin_manage:admin_manage_dashboard')
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
    print(f"[DEBUG] Redirect URI being sent to Google: {settings.GOOGLE_REDIRECT_URI}")
    # Tạo Google OAuth URL
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    return redirect(auth_url)

def google_callback(request):
    """Xử lý callback từ Google"""
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
        print(f"[GOOGLE DEBUG] Received code: {code[:20]}...")
        
        # 1. Đổi code lấy access token
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
        print(f"[GOOGLE DEBUG] Requesting token from Google...")
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data, timeout=10)
        print(f"[GOOGLE DEBUG] Token response status: {token_response.status_code}")
        
        if token_response.status_code != 200:
            print(f"[GOOGLE DEBUG] Token error: {token_response.text}")
            messages.error(request, "Không thể lấy token từ Google")
            return redirect('users:login_form')
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        print(f"[GOOGLE DEBUG] Got access token")
        
        # 2. Lấy thông tin user từ Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        print(f"[GOOGLE DEBUG] User info response status: {user_info_response.status_code}")
        
        if user_info_response.status_code != 200:
            print(f"[GOOGLE DEBUG] User info error: {user_info_response.text}")
            messages.error(request, "Không thể lấy thông tin từ Google")
            return redirect('users:login_form')
        
        user_info = user_info_response.json()
        print(f"[GOOGLE DEBUG] User info: {user_info}")
        
        # 3. Xử lý thông tin user
        google_id = user_info.get('sub')  # Google user ID
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        if not email:
            messages.error(request, "Google không cung cấp email")
            return redirect('users:login_form')
        
        print(f"[GOOGLE DEBUG] Processing user with email: {email}, google_id: {google_id}")
        
        # 4. Kiểm tra xem social account đã tồn tại chưa
        try:
            social_account = SocialAccount.objects.get(
                provider='google', 
                provider_id=google_id
            )
            user = social_account.user
            print(f"[GOOGLE DEBUG] Found existing social account for user: {user.username}")
            
        except SocialAccount.DoesNotExist:
            print(f"[GOOGLE DEBUG] No social account found, checking email...")
            
            # 5. Kiểm tra xem email đã có trong hệ thống chưa
            try:
                user = User.objects.get(email=email)
                print(f"[GOOGLE DEBUG] Found existing user by email: {user.username}")
                
                # Tạo liên kết Google với tài khoản hiện có
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    provider_id=google_id,
                    email=email
                )
                messages.info(request, "Đã liên kết tài khoản Google với tài khoản hiện có")
                
            except User.DoesNotExist:
                print(f"[GOOGLE DEBUG] No user found, creating new user...")
                
                # 6. Tạo user mới
                # Tạo username từ email
                username_base = email.split('@')[0]
                username = username_base
                counter = 1
                
                # Đảm bảo username là unique
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1
                
                print(f"[GOOGLE DEBUG] Creating user with username: {username}")
                
                # Tạo user mới
                user = User.objects.create(
                    username=username,
                    email=email,
                    password=make_password(None),  # Không cần password
                    fullname=name,
                    role="user"
                )
                print(f"[GOOGLE DEBUG] User created: {user.user_id}")
                
                try:
                    print(f"[GOOGLE DEBUG] Creating ToDoList...")
                    from all_app.to_do_list.to_do_list_models import ToDoList
                    todo = ToDoList.objects.create(user=user)
                    print(f"[GOOGLE DEBUG] ToDoList created: {todo.todolist_id}")
                    
                    print(f"[GOOGLE DEBUG] Creating Flashcard...")
                    from all_app.flashcards.flashcards_models import Flashcard  
                    flashcard = Flashcard.objects.create(user=user)
                    print(f"[GOOGLE DEBUG] Flashcard created: {flashcard.flashcard_id}")
                    
                    print(f"[GOOGLE DEBUG] Creating Habit...")
                    from all_app.habit.habit_models import Habit
                    habit = Habit.objects.create(user=user)
                    print(f"[GOOGLE DEBUG] Habit created: {habit.habit_id}")
                    
                    print(f"[GOOGLE DEBUG] Creating Pomodoro...")
                    from all_app.pomodoro.pomodoro_models import Pomodoro
                    pomodoro = Pomodoro.objects.create(user=user, title="My Pomodoro")
                    print(f"[GOOGLE DEBUG] Pomodoro created: {pomodoro.pomodoro_id}")
                    
                    print(f"[GOOGLE DEBUG] Creating Calendar...")
                    from all_app.calendar_app.calendar_models import Calendar
                    calendar = Calendar.objects.create(user=user, name="My Calendar")
                    print(f"[GOOGLE DEBUG] Calendar created: {calendar.calendar_id}")
                    
                except Exception as model_error:
                    print(f"[GOOGLE DEBUG ERROR] Failed to create related data: {model_error}")
                    import traceback
                    traceback.print_exc()
                    # Nếu tạo dữ liệu thất bại, xóa user
                    user.delete()
                    messages.error(request, "Không thể thiết lập tài khoản. Vui lòng thử lại.")
                    return redirect('users:login_form')
                
                # Tạo social account
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    provider_id=google_id,
                    email=email
                )
                print(f"[GOOGLE DEBUG] Social account created")
                
                messages.success(request, "Đã tạo tài khoản mới với Google")

        # 7. Đăng nhập user (set session)
        print(f"[GOOGLE DEBUG] Setting session for user: {user.user_id}")
        request.session['user_id'] = str(user.user_id)
        request.session['role'] = user.role
        
        # Kiểm tra lại xem ToDoList có tồn tại không
        from all_app.to_do_list.to_do_list_models import ToDoList
        if ToDoList.objects.filter(user=user).exists():
            print(f"[GOOGLE DEBUG] ToDoList exists for user")
        else:
            print(f"[GOOGLE DEBUG] ERROR: ToDoList does NOT exist for user!")
            # Tạo ngay lập tức
            ToDoList.objects.create(user=user)
            print(f"[GOOGLE DEBUG] Created ToDoList in session")
        
        messages.success(request, f"Đăng nhập thành công với {email}")
        
        # 8. Redirect về trang chủ
        if user.role == "admin":
            print(f"[GOOGLE DEBUG] Redirecting to admin dashboard")
            return redirect('admin_manage:admin_manage_dashboard')
        else:
            print(f"[GOOGLE DEBUG] Redirecting to todo home")
            return redirect('to_do_list:home')
            
    except requests.Timeout:
        print(f"[GOOGLE DEBUG] Request timeout")
        messages.error(request, "Kết nối với Google quá thời gian chờ")
        return redirect('users:login_form')
    except requests.RequestException as e:
        print(f"[GOOGLE DEBUG] Request error: {e}")
        messages.error(request, f"Lỗi kết nối: {str(e)}")
        return redirect('users:login_form')
    except Exception as e:
        print(f"[GOOGLE DEBUG] General error: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Lỗi hệ thống: {str(e)}")
        return redirect('users:login_form')
    

