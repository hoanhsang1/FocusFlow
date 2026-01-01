# all_app/dashboard/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import date, timedelta, datetime
import json
from all_app.users.check_login_role import *
from .models import DashboardSettings, UserActivity, DailyStats
from all_app.pomodoro.pomodoro_models import PomodoroHistory, Pomodoro
from all_app.to_do_list.to_do_list_models import Task, ToDoList
from all_app.calendar_app.models import Event
from all_app.habit.models import Habit, HabitListLog
from all_app.flashcards.flashcards_models import FlashcardSet, FlashcardProgress

@role_required('user')
def dashboard_home(request):
    """Trang dashboard chính - HOME PAGE"""
    user = request.user
    today = timezone.now().date()
    
    # Lấy hoặc tạo dashboard settings
    settings, created = DashboardSettings.objects.get_or_create(
        user=user,
        defaults={
            'layout_config': {},
            'widget_order': ['pomodoro', 'todo', 'calendar', 'habits', 'flashcards', 'productivity']
        }
    )
    
    # 1. THỐNG KÊ POMODORO
    pomodoro_stats = get_pomodoro_stats(user, today)
    
    # 2. THỐNG KÊ TASK
    todo_stats = get_todo_stats(user, today)
    
    # 3. SỰ KIỆN SẮP TỚI
    upcoming_events = get_upcoming_events(user, today)
    
    # 4. THÓI QUEN HÔM NAY
    habits_today = get_habits_today(user, today)
    
    # 5. THỐNG KÊ FLASHCARD
    flashcard_stats = get_flashcard_stats(user, today)
    
    # 6. ĐIỂM NĂNG SUẤT
    productivity_stats = get_productivity_stats(user, today)
    
    # 7. HOẠT ĐỘNG GẦN ĐÂY
    recent_activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:10]
    
    # 8. THỐNG KÊ TUẦN
    weekly_stats = get_weekly_stats(user, today)
    
    context = {
        'user': user,
        'today': today,
        'settings': settings,
        
        # Thống kê
        'pomodoro_stats': pomodoro_stats,
        'todo_stats': todo_stats,
        'upcoming_events': upcoming_events,
        'habits_today': habits_today,
        'flashcard_stats': flashcard_stats,
        'productivity_stats': productivity_stats,
        'recent_activities': recent_activities,
        'weekly_stats': weekly_stats,
        
        # Widget visibility
        'show_pomodoro': settings.show_pomodoro,
        'show_todo': settings.show_todo,
        'show_calendar': settings.show_calendar,
        'show_habits': settings.show_habits,
        'show_flashcards': settings.show_flashcards,
        'show_productivity': settings.show_productivity,
    }
    
    return render(request, 'dashboard/home.html', context)

def get_pomodoro_stats(user, today):
    """Lấy thống kê pomodoro"""
    week_start = today - timedelta(days=today.weekday())
    
    stats = {
        'today_sessions': PomodoroHistory.objects.filter(user=user, date=today).count(),
        'week_sessions': PomodoroHistory.objects.filter(
            user=user, 
            date__gte=week_start
        ).count(),
        'total_sessions': PomodoroHistory.objects.filter(user=user).count(),
        'today_minutes': PomodoroHistory.objects.filter(
            user=user, 
            date=today
        ).aggregate(total=Sum('duration'))['total'] or 0,
        'active_session': Pomodoro.objects.filter(
            user=user, 
            status='running'
        ).first(),
        'recent_sessions': PomodoroHistory.objects.filter(
            user=user
        ).order_by('-date', '-start_time')[:5],
    }
    
    # Tính trung bình
    avg = PomodoroHistory.objects.filter(
        user=user,
        date__gte=week_start
    ).values('date').annotate(count=Count('history_id')).aggregate(Avg('count'))['count__avg'] or 0
    
    stats['avg_daily_sessions'] = round(avg, 1)
    
    return stats

def get_todo_stats(user, today):
    """Lấy thống kê todo"""
    tomorrow = today + timedelta(days=1)
    
    stats = {
        'total_tasks': Task.objects.filter(todo_list__user=user).count(),
        'completed_today': Task.objects.filter(
            todo_list__user=user,
            completed=True,
            updated_at__date=today
        ).count(),
        'pending_tasks': Task.objects.filter(
            todo_list__user=user,
            completed=False
        ).count(),
        'urgent_tasks': Task.objects.filter(
            todo_list__user=user,
            completed=False,
            due_date__lte=tomorrow
        ).count(),
        'overdue_tasks': Task.objects.filter(
            todo_list__user=user,
            completed=False,
            due_date__lt=today
        ).count(),
        'recent_tasks': Task.objects.filter(
            todo_list__user=user,
            completed=False
        ).order_by('due_date')[:5],
    }
    
    return stats

def get_upcoming_events(user, today):
    """Lấy sự kiện sắp tới"""
    events = Event.objects.filter(
        calendar__user=user,
        start_time__date__gte=today
    ).order_by('start_time')[:5]
    
    return events

def get_habits_today(user, today):
    """Lấy thói quen cho hôm nay"""
    habits = Habit.objects.filter(
        user=user,
        is_active=True
    ).annotate(
        today_logged=Count('habitlist__habitlistlog', 
                          filter=Q(habitlist__habitlistlog__date=today))
    )[:5]
    
    # Thêm thông tin log cho mỗi habit
    for habit in habits:
        today_log = HabitListLog.objects.filter(
            habit_list__habit=habit,
            date=today
        ).first()
        habit.today_status = today_log.status if today_log else 'pending'
    
    return habits

def get_flashcard_stats(user, today):
    """Lấy thống kê flashcard"""
    stats = {
        'total_sets': FlashcardSet.objects.filter(user=user).count(),
        'due_for_review': FlashcardProgress.objects.filter(
            flashcard__flashcard_set__user=user,
            next_review__lte=today
        ).count(),
        'reviewed_today': FlashcardProgress.objects.filter(
            flashcard__flashcard_set__user=user,
            last_reviewed__date=today
        ).count(),
        'total_cards': FlashcardSet.objects.filter(user=user).aggregate(
            total=Sum('cards__count')
        )['total'] or 0,
    }
    
    return stats

def get_productivity_stats(user, today):
    """Lấy thống kê năng suất"""
    # Lấy hoặc tạo daily stats
    daily_stats = DailyStats.get_or_create_today(user)
    
    stats = {
        'today_score': daily_stats.productivity_score,
        'streak_days': calculate_streak_days(user),
        'weekly_average': get_weekly_average_score(user, today),
        'goals_completed': calculate_goals_completed(user, today),
    }
    
    return stats

def get_weekly_stats(user, today):
    """Lấy thống kê tuần"""
    week_start = today - timedelta(days=today.weekday())
    
    # Thống kê pomodoro theo ngày trong tuần
    pomodoro_by_day = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        count = PomodoroHistory.objects.filter(user=user, date=day).count()
        pomodoro_by_day.append({
            'day': day.strftime('%a'),
            'count': count
        })
    
    # Tổng tasks hoàn thành trong tuần
    tasks_completed_week = Task.objects.filter(
        todo_list__user=user,
        completed=True,
        updated_at__date__gte=week_start
    ).count()
    
    # Tổng habits hoàn thành trong tuần
    habits_completed_week = HabitListLog.objects.filter(
        habit_list__habit__user=user,
        date__gte=week_start,
        status='completed'
    ).count()
    
    return {
        'pomodoro_by_day': pomodoro_by_day,
        'tasks_completed': tasks_completed_week,
        'habits_completed': habits_completed_week,
        'week_start': week_start,
        'week_end': week_start + timedelta(days=6),
    }

def calculate_streak_days(user):
    """Tính số ngày liên tiếp có hoạt động"""
    today = timezone.now().date()
    streak = 0
    
    for i in range(30):  # Kiểm tra 30 ngày gần nhất
        check_date = today - timedelta(days=i)
        has_activity = (
            PomodoroHistory.objects.filter(user=user, date=check_date).exists() or
            Task.objects.filter(todo_list__user=user, completed=True, updated_at__date=check_date).exists() or
            HabitListLog.objects.filter(habit_list__habit__user=user, date=check_date, status='completed').exists()
        )
        
        if has_activity:
            streak += 1
        else:
            break
    
    return streak

def get_weekly_average_score(user, today):
    """Tính điểm trung bình tuần"""
    week_start = today - timedelta(days=today.weekday())
    
    weekly_scores = DailyStats.objects.filter(
        user=user,
        date__gte=week_start
    ).values_list('productivity_score', flat=True)
    
    if weekly_scores:
        return sum(weekly_scores) / len(weekly_scores)
    return 0

def calculate_goals_completed(user, today):
    """Tính tỷ lệ hoàn thành mục tiêu"""
    # Mục tiêu mặc định
    goals = {
        'pomodoro': 4,  # 4 sessions/ngày
        'tasks': 5,     # 5 tasks/ngày
        'habits': 3,    # 3 habits/ngày
    }
    
    # Thực tế
    actual = {
        'pomodoro': PomodoroHistory.objects.filter(user=user, date=today).count(),
        'tasks': Task.objects.filter(
            todo_list__user=user,
            completed=True,
            updated_at__date=today
        ).count(),
        'habits': HabitListLog.objects.filter(
            habit_list__habit__user=user,
            date=today,
            status='completed'
        ).count(),
    }
    
    # Tính tỷ lệ
    completed = 0
    for key in goals:
        if actual[key] >= goals[key]:
            completed += 1
    
    return {
        'completed': completed,
        'total': len(goals),
        'percentage': int((completed / len(goals)) * 100) if goals else 0
    }

# API VIEWS

@role_required('user')
def update_widget_settings(request):
    """API cập nhật cài đặt widget"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            settings, created = DashboardSettings.objects.get_or_create(user=request.user)
            
            # Cập nhật các trường
            if 'show_pomodoro' in data:
                settings.show_pomodoro = data['show_pomodoro']
            if 'show_todo' in data:
                settings.show_todo = data['show_todo']
            if 'show_calendar' in data:
                settings.show_calendar = data['show_calendar']
            if 'show_habits' in data:
                settings.show_habits = data['show_habits']
            if 'show_flashcards' in data:
                settings.show_flashcards = data['show_flashcards']
            if 'show_productivity' in data:
                settings.show_productivity = data['show_productivity']
            if 'widget_order' in data:
                settings.widget_order = data['widget_order']
            if 'theme' in data:
                settings.theme = data['theme']
            
            settings.save()
            
            # Log activity
            UserActivity.log_activity(
                user=request.user,
                activity_type='settings_update',
                description='Updated dashboard settings',
                metadata={'settings': data}
            )
            
            return JsonResponse({'status': 'success', 'message': 'Settings updated'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@role_required('user')
def get_quick_stats(request):
    """API lấy thống kê nhanh (cho real-time updates)"""
    user = request.user
    today = timezone.now().date()
    
    stats = {
        'pomodoro_today': PomodoroHistory.objects.filter(user=user, date=today).count(),
        'tasks_completed': Task.objects.filter(
            todo_list__user=user,
            completed=True,
            updated_at__date=today
        ).count(),
        'habits_completed': HabitListLog.objects.filter(
            habit_list__habit__user=user,
            date=today,
            status='completed'
        ).count(),
        'flashcards_reviewed': FlashcardProgress.objects.filter(
            flashcard__flashcard_set__user=user,
            last_reviewed__date=today
        ).count(),
    }
    
    return JsonResponse(stats)


@role_required('user')
def quick_add_task(request):
    """API thêm task nhanh từ dashboard"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        
        if title:
            # Tạo task trong nhóm mặc định hoặc tạo mới
            todo_list, created = ToDoList.objects.get_or_create(
                user=request.user,
                title="Quick Tasks",
                defaults={'description': 'Tasks added from dashboard'}
            )
            
            task = Task.objects.create(
                todo_list=todo_list,
                title=title,
                description=f"Added from dashboard at {timezone.now().strftime('%H:%M')}",
                priority='medium'
            )
            
            # Log activity
            UserActivity.log_activity(
                user=request.user,
                activity_type='task_create',
                description=f'Created task: {title}',
                metadata={'task_id': task.task_id, 'source': 'dashboard'}
            )
            
            # Update daily stats
            stats = DailyStats.get_or_create_today(request.user)
            stats.tasks_created += 1
            stats.calculate_score()
            
            return JsonResponse({
                'status': 'success',
                'task_id': task.task_id,
                'title': task.title
            })
    
    return JsonResponse({'status': 'error', 'message': 'Title is required'}, status=400)


@role_required('user')
def update_habit_status(request, habit_id):
    """API cập nhật trạng thái habit"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status', 'completed')
            log_date = data.get('date', timezone.now().date())
            
            # Tìm hoặc tạo habit log
            habit = Habit.objects.get(habit_id=habit_id, user=request.user)
            habit_list = habit.habitlist_set.first()
            
            if habit_list:
                log, created = HabitListLog.objects.get_or_create(
                    habit_list=habit_list,
                    date=log_date,
                    defaults={'status': status}
                )
                
                if not created:
                    log.status = status
                    log.save()
                
                # Log activity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='habit_complete',
                    description=f'Updated habit: {habit.name} to {status}',
                    metadata={'habit_id': habit_id, 'status': status}
                )
                
                # Update daily stats
                stats = DailyStats.get_or_create_today(request.user)
                if status == 'completed':
                    stats.habits_completed += 1
                stats.calculate_score()
                
                return JsonResponse({'status': 'success', 'habit_status': status})
            
        except Habit.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Habit not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@role_required('user')
def get_recent_activity(request):
    """API lấy hoạt động gần đây"""
    activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:15]
    
    activity_list = []
    for activity in activities:
        activity_list.append({
            'id': activity.user,
            'type': activity.activity_type,
            'type_display': activity.get_activity_type_display(),
            'description': activity.description,
            'icon': get_activity_icon(activity.activity_type),
            'color': get_activity_color(activity.activity_type),
            'time': activity.created_at.strftime('%H:%M'),
            'date': activity.created_at.strftime('%b %d'),
            'metadata': activity.metadata,
        })
    
    return JsonResponse({'activities': activity_list})

def get_activity_icon(activity_type):
    """Lấy icon cho loại activity"""
    icons = {
        'pomodoro_start': 'fas fa-play-circle',
        'pomodoro_complete': 'fas fa-flag-checkered',
        'task_create': 'fas fa-plus-circle',
        'task_complete': 'fas fa-check-circle',
        'habit_complete': 'fas fa-star',
        'flashcard_review': 'fas fa-brain',
        'event_create': 'fas fa-calendar-plus',
        'login': 'fas fa-sign-in-alt',
        'settings_update': 'fas fa-cog',
    }
    return icons.get(activity_type, 'fas fa-circle')

def get_activity_color(activity_type):
    """Lấy màu cho loại activity"""
    colors = {
        'pomodoro_start': 'primary',
        'pomodoro_complete': 'success',
        'task_create': 'info',
        'task_complete': 'success',
        'habit_complete': 'warning',
        'flashcard_review': 'purple',
        'event_create': 'info',
        'login': 'secondary',
        'settings_update': 'secondary',
    }
    return colors.get(activity_type, 'secondary')