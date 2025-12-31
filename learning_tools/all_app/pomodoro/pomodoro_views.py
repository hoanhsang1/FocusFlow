from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .pomodoro_models import Pomodoro, PomodoroHistory, PomodoroSettings

# ==================== MAIN PAGES ====================

def pomodoro_home(request):
    """
    Trang chủ Pomodoro
    """
    if 'user_id' not in request.session:
        return redirect('users:login_form')
    
    user_id = request.session['user_id']
    
    # Lấy tất cả pomodoros của user
    pomodoros = Pomodoro.objects.filter(user_id=user_id).order_by('-created_at')
    
    # Lấy pomodoro đang active
    active_pomodoro = pomodoros.filter(status='running').first()
    if not active_pomodoro:
        active_pomodoro = pomodoros.filter(status='paused').first()
    
    # Lấy lịch sử gần đây (không bị xóa)
    recent_history = PomodoroHistory.objects.filter(
        pomodoro__user_id=user_id,
        is_deleted=False
    ).order_by('-start_time')[:10]
    
    # Thống kê hôm nay
    today = timezone.now().date()
    today_history = PomodoroHistory.objects.filter(
        pomodoro__user_id=user_id,
        start_time__date=today,
        is_deleted=False,
        status='completed'
    )
    
    today_stats = {
        'sessions': today_history.count(),
        'total_minutes': sum(h.duration_minutes for h in today_history),
        'avg_duration': today_history.aggregate(models.Avg('duration_minutes'))['duration_minutes__avg'] or 0
    }
    
    # Lấy settings
    try:
        settings = PomodoroSettings.objects.get(user_id=user_id)
    except PomodoroSettings.DoesNotExist:
        settings = PomodoroSettings.objects.create(
            user_id=user_id,
            default_work_duration=25,
            default_break_duration=5
        )
    
    context = {
        'pomodoros': pomodoros,
        'active_pomodoro': active_pomodoro,
        'recent_history': recent_history,
        'today_stats': today_stats,
        'settings': settings,
        'page': 'pomodoro'
    }
    
    return render(request, 'pomodoro/home.html', context)


def pomodoro_detail(request, pomodoro_id):
    """
    Chi tiết một Pomodoro
    """
    if 'user_id' not in request.session:
        return redirect('users:login_form')
    
    user_id = request.session['user_id']
    pomodoro = get_object_or_404(Pomodoro, pomodoro_id=pomodoro_id, user_id=user_id)
    
    # Lấy lịch sử của pomodoro này
    history = PomodoroHistory.objects.filter(
        pomodoro=pomodoro,
        is_deleted=False
    ).order_by('-start_time')
    
    context = {
        'pomodoro': pomodoro,
        'history': history,
        'page': 'pomodoro_detail'
    }
    
    return render(request, 'pomodoro/detail.html', context)


def pomodoro_history(request):
    """
    Xem toàn bộ lịch sử Pomodoro
    """
    if 'user_id' not in request.session:
        return redirect('users:login_form')
    
    user_id = request.session['user_id']
    
    # Lấy tham số filter
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    status_filter = request.GET.get('status')
    
    # Query lịch sử
    history = PomodoroHistory.objects.filter(
        pomodoro__user_id=user_id,
        is_deleted=False
    )
    
    # Áp dụng filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            history = history.filter(start_time__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            history = history.filter(start_time__date__lte=to_date)
        except ValueError:
            pass
    
    if status_filter:
        history = history.filter(status=status_filter)
    
    history = history.order_by('-start_time')
    
    # Tính toán thống kê
    total_sessions = history.count()
    total_minutes = sum(h.duration_minutes for h in history)
    completed_sessions = history.filter(status='completed').count()
    
    context = {
        'history': history,
        'total_sessions': total_sessions,
        'total_minutes': total_minutes,
        'completed_sessions': completed_sessions,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'page': 'pomodoro_history'
    }
    
    return render(request, 'pomodoro/history.html', context)

# ==================== API ENDPOINTS ====================

@csrf_exempt
@require_http_methods(["POST"])
def api_create_pomodoro(request):
    """
    API: Tạo Pomodoro mới
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user_id = request.session['user_id']
        
        # Tạo pomodoro mới
        pomodoro = Pomodoro.objects.create(
            user_id=user_id,
            title=data.get('title', 'New Pomodoro'),
            work_duration=data.get('work_duration', 25),
            break_duration=data.get('break_duration', 5)
        )
        
        return JsonResponse({
            'success': True,
            'pomodoro_id': pomodoro.pomodoro_id,
            'title': pomodoro.title,
            'message': 'Pomodoro created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_start_pomodoro(request):
    """
    API: Bắt đầu Pomodoro
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user_id = request.session['user_id']
        pomodoro_id = data.get('pomodoro_id')
        
        pomodoro = Pomodoro.objects.get(pomodoro_id=pomodoro_id, user_id=user_id)
        pomodoro.start_timer()
        
        return JsonResponse({
            'success': True,
            'status': pomodoro.status,
            'current_session': pomodoro.current_session,
            'duration': pomodoro.get_current_duration(),
            'message': 'Pomodoro started'
        })
        
    except Pomodoro.DoesNotExist:
        return JsonResponse({'error': 'Pomodoro not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_pause_pomodoro(request):
    """
    API: Tạm dừng Pomodoro
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user_id = request.session['user_id']
        pomodoro_id = data.get('pomodoro_id')
        
        pomodoro = Pomodoro.objects.get(pomodoro_id=pomodoro_id, user_id=user_id)
        pomodoro.pause_timer()
        
        return JsonResponse({
            'success': True,
            'status': pomodoro.status,
            'message': 'Pomodoro paused'
        })
        
    except Pomodoro.DoesNotExist:
        return JsonResponse({'error': 'Pomodoro not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_stop_pomodoro(request):
    """
    API: Dừng Pomodoro
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user_id = request.session['user_id']
        pomodoro_id = data.get('pomodoro_id')
        
        pomodoro = Pomodoro.objects.get(pomodoro_id=pomodoro_id, user_id=user_id)
        pomodoro.stop_timer()
        
        return JsonResponse({
            'success': True,
            'status': pomodoro.status,
            'sessions_completed': pomodoro.sessions_completed,
            'message': 'Pomodoro stopped'
        })
        
    except Pomodoro.DoesNotExist:
        return JsonResponse({'error': 'Pomodoro not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_complete_session(request):
    """
    API: Hoàn thành session hiện tại
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user_id = request.session['user_id']
        pomodoro_id = data.get('pomodoro_id')
        
        pomodoro = Pomodoro.objects.get(pomodoro_id=pomodoro_id, user_id=user_id)
        pomodoro.complete_session()
        
        # Nếu auto_start_break được bật, tự động start session tiếp theo
        try:
            settings = PomodoroSettings.objects.get(user_id=user_id)
            if settings.auto_start_break:
                pomodoro.start_timer()
        except PomodoroSettings.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'current_session': pomodoro.current_session,
            'sessions_completed': pomodoro.sessions_completed,
            'message': 'Session completed'
        })
        
    except Pomodoro.DoesNotExist:
        return JsonResponse({'error': 'Pomodoro not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_settings(request):
    """
    API: Cập nhật cài đặt Pomodoro
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user_id = request.session['user_id']
        
        # Lấy hoặc tạo settings
        settings, created = PomodoroSettings.objects.get_or_create(
            user_id=user_id,
            defaults={
                'default_work_duration': 25,
                'default_break_duration': 5,
                'enable_sounds': True,
                'enable_notifications': True
            }
        )
        
        # Cập nhật các field
        update_fields = [
            'default_work_duration', 'default_break_duration',
            'auto_start_break', 'enable_sounds', 'enable_notifications',
            'theme'
        ]
        
        for field in update_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def api_get_pomodoro_status(request, pomodoro_id):
    """
    API: Lấy trạng thái Pomodoro
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user_id = request.session['user_id']
        pomodoro = Pomodoro.objects.get(pomodoro_id=pomodoro_id, user_id=user_id)
        
        # Tính thời gian đã trôi qua nếu đang running
        elapsed_minutes = 0
        if pomodoro.status == 'running':
            # Tìm history record gần nhất
            history = PomodoroHistory.objects.filter(
                pomodoro=pomodoro,
                end_time__isnull=True
            ).order_by('-start_time').first()
            
            if history:
                elapsed = (timezone.now() - history.start_time).total_seconds() / 60
                elapsed_minutes = int(elapsed)
        
        return JsonResponse({
            'success': True,
            'pomodoro': {
                'id': pomodoro.pomodoro_id,
                'title': pomodoro.title,
                'status': pomodoro.status,
                'current_session': pomodoro.current_session,
                'work_duration': pomodoro.work_duration,
                'break_duration': pomodoro.break_duration,
                'sessions_completed': pomodoro.sessions_completed,
                'elapsed_minutes': elapsed_minutes,
                'remaining_minutes': max(0, pomodoro.get_current_duration() - elapsed_minutes)
            }
        })
        
    except Pomodoro.DoesNotExist:
        return JsonResponse({'error': 'Pomodoro not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_history(request, history_id):
    """
    API: Xóa lịch sử (soft delete)
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user_id = request.session['user_id']
        history = PomodoroHistory.objects.get(
            history_id=history_id,
            pomodoro__user_id=user_id
        )
        
        history.soft_delete()
        
        return JsonResponse({
            'success': True,
            'message': 'History deleted'
        })
        
    except PomodoroHistory.DoesNotExist:
        return JsonResponse({'error': 'History not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def api_get_statistics(request):
    """
    API: Lấy thống kê Pomodoro
    """
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user_id = request.session['user_id']
        
        # Lấy dữ liệu 7 ngày gần nhất
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        history = PomodoroHistory.objects.filter(
            pomodoro__user_id=user_id,
            start_time__range=(start_date, end_date),
            is_deleted=False,
            status='completed'
        )
        
        # Thống kê theo ngày
        daily_stats = []
        for i in range(7):
            date = (end_date - timedelta(days=i)).date()
            day_history = history.filter(start_time__date=date)
            
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'sessions': day_history.count(),
                'total_minutes': sum(h.duration_minutes for h in day_history),
                'avg_duration': day_history.aggregate(models.Avg('duration_minutes'))['duration_minutes__avg'] or 0
            })
        
        # Thống kê tổng
        total_stats = {
            'total_sessions': history.count(),
            'total_minutes': sum(h.duration_minutes for h in history),
            'avg_minutes_per_day': sum(h.duration_minutes for h in history) / 7 if history.count() > 0 else 0,
            'completion_rate': (history.count() / (history.count() + PomodoroHistory.objects.filter(
                pomodoro__user_id=user_id,
                start_time__range=(start_date, end_date),
                is_deleted=False,
                status='interrupted'
            ).count())) * 100 if history.count() > 0 else 0
        }
        
        return JsonResponse({
            'success': True,
            'daily_stats': daily_stats,
            'total_stats': total_stats
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)