# all_app/admin_manage/admin_manage_views.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import sys
import django
import platform
from all_app.users.check_login_role import *


from all_app.to_do_list.to_do_list_models import ToDoList, ToDoListGroup, Task
from all_app.users.users_models import User
@role_required("admin")
def admin_manage_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        # User stats - SỬA: Chỉ dùng các field có sẵn trong User
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_deleted=False).count(),
        'new_users_week': User.objects.filter(created_at__gte=week_ago).count(),
        'new_users_month': User.objects.filter(created_at__gte=month_ago).count(),
        
        # Group stats - SỬA: Dùng trực tiếp từ ToDoListGroup
        'total_groups': ToDoListGroup.objects.count(),
        'active_groups': ToDoListGroup.objects.filter(is_deleted=False).count(),
        'deleted_groups': ToDoListGroup.objects.filter(is_deleted=False).count(),
        
        # Task stats - SỬA: Dùng trực tiếp từ Task
        'total_tasks': Task.objects.count(),
        'pending_tasks': Task.objects.filter(status='pending', is_deleted=False).count(),
        'completed_tasks': Task.objects.filter(status='completed', is_deleted=False).count(),
        'overdue_tasks': Task.objects.filter(
            deadline__lt=today, 
            status='pending', 
            is_deleted=False
        ).count(),
        'deleted_tasks': Task.objects.filter(is_deleted=False).count(),
    }
    
    # Recent activity - SỬA: Đơn giản hóa query
    recent_tasks = Task.objects.filter(
        is_deleted=False
    ).select_related('group').order_by('-created_at')[:10]
    
    # Top active users - SỬA: Sử dụng query đúng
    # Cách 1: Nếu có relation từ User → ToDoList
    try:
        top_users = User.objects.annotate(
            task_count=Count('todolist__todolistgroup__task')
        ).filter(task_count__gt=0).order_by('-task_count')[:5]
    except:
        # Cách 2: Fallback - lấy user mới nhất
        top_users = User.objects.all().order_by('-created_at')[:5]
    
    # Recent registered users
    recent_users = User.objects.all().order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_tasks': recent_tasks,
        'top_users': top_users,
        'recent_users': recent_users,
        'today': today,
    }
    return render(request, 'admin_manage/dashboard.html', context)
@role_required("admin")
def admin_manage_users(request):
    users = User.objects.all().order_by('username')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(fullname__icontains=search_query) |
            Q(created_at__icontains=search_query)
        )
    
    # Tính thống kê SAU KHI filter search
    user_stats = []
    for user in users:
        try:
            todolist_count = user.todolist_set.count() if hasattr(user, 'todolist_set') else 0
            task_count = Task.objects.filter(group__todolist__user=user).count()
        except:
            todolist_count = 0
            task_count = 0
            
        user_stats.append({
            'user': user,
            'todolist_count': todolist_count,
            'task_count': task_count
        })
    
    context = {
        'users': users,
        'user_stats': user_stats,
        'search_query': search_query,
        'total_users': users.count()
    }
    return render(request, 'admin_manage/user_management.html', context)
@role_required("admin")
def admin_manage_groups(request):
    groups = ToDoListGroup.objects.select_related(
        'todolist', 'todolist__user'
    ).annotate(
        task_count=Count('task', filter=Q(task__is_deleted=False)),
        completed_tasks=Count('task', filter=Q(task__status='completed', task__is_deleted=False)),
        pending_tasks=Count('task', filter=Q(task__status='pending', task__is_deleted=False))
    ).order_by('-created_at')
    
    # Filter options
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        groups = groups.filter(is_deleted=False)
    elif status_filter == 'deleted':
        groups = groups.filter(is_deleted=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        groups = groups.filter(title__icontains=search_query)
    
    context = {
        'groups': groups,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_groups': groups.count()
    }
    return render(request, 'admin_manage/group_management.html', context)

@role_required("admin")
def admin_manage_tasks(request):
    tasks = Task.objects.select_related(
        'group', 'group__todolist', 'group__todolist__user'
    ).order_by('-created_at')
    
    # Filter options
    status_filter = request.GET.get('status', 'all')
    deletion_filter = request.GET.get('deletion', 'active')
    
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    if deletion_filter == 'active':
        tasks = tasks.filter(is_deleted=False)
    elif deletion_filter == 'deleted':
        tasks = tasks.filter(is_deleted=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'deletion_filter': deletion_filter,
        'search_query': search_query,
        'total_tasks': tasks.count()
    }
    return render(request, 'admin_manage/task_management.html', context)


@role_required("admin")
def admin_manage_system(request):
    
    system_info = {
        'python_version': sys.version.split()[0],  # Chỉ lấy version number
        'django_version': django.get_version(),  # SỬA: dùng get_version()
        'platform': platform.platform(),
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'time_zone': settings.TIME_ZONE,
    }
    
    context = {
        'system_info': system_info
    }
    return render(request, 'admin_manage/system_info.html', context)


@role_required("admin")
def admin_manage_analytics(request):
    # Date range for analytics
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Tasks created per day (last 30 days) - SỬA: dùng 'task_id' thay vì 'id'
    from django.db.models.functions import TruncDate
    
    daily_tasks = Task.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('task_id')  # SỬA: 'task_id' thay vì 'id'
    ).order_by('date')
    
    # Status distribution - SỬA: dùng 'task_id'
    status_distribution = Task.objects.filter(
        is_deleted=False
    ).values('status').annotate(
        count=Count('task_id')  # SỬA: 'task_id' thay vì 'id'
    ).order_by('-count')
    
    # User activity - SỬA: Đơn giản hóa
    user_activity = []
    all_users = User.objects.all()[:10]
    
    for user in all_users:
        try:
            # Tính task count bằng cách khác
            task_count = Task.objects.filter(
                group__todolist__user=user,
                is_deleted=False
            ).count()
            
            group_count = ToDoListGroup.objects.filter(
                todolist__user=user,
                is_deleted=False
            ).count()
            
            user_activity.append({
                'username': user.username,
                'task_count': task_count,
                'group_count': group_count
            })
        except Exception as e:
            print(f"Error calculating stats for user {user.username}: {e}")
            user_activity.append({
                'username': user.username,
                'task_count': 0,
                'group_count': 0
            })
    
    # Sắp xếp theo task_count giảm dần
    user_activity = sorted(user_activity, key=lambda x: x['task_count'], reverse=True)[:10]
    
    # Completion rate by group - SỬA: Đơn giản hóa
    group_completion = []
    all_groups = ToDoListGroup.objects.filter(is_deleted=False)[:20]
    
    for group in all_groups:
        try:
            total_tasks = Task.objects.filter(group=group, is_deleted=False).count()
            completed_tasks = Task.objects.filter(group=group, status='completed', is_deleted=False).count()
            
            if total_tasks > 0:
                completion_rate = (completed_tasks / total_tasks) * 100
            else:
                completion_rate = 0
                
            group_completion.append({
                'title': group.title,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate
            })
        except Exception as e:
            print(f"Error calculating completion for group {group.title}: {e}")
            continue
    
    # Sắp xếp theo completion rate giảm dần
    group_completion = sorted(group_completion, key=lambda x: x['completion_rate'], reverse=True)[:10]
    
    context = {
        'daily_tasks': list(daily_tasks),
        'status_distribution': list(status_distribution),
        'user_activity': user_activity,
        'group_completion': group_completion,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'admin_manage/analytics.html', context)
