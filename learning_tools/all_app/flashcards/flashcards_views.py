from datetime import timezone
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from all_app.users.check_login_role import *
from .flashcards_models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.views.decorators.http import require_POST
import json
from django.utils import timezone
from all_app.users.users_models import User

# Create your views here.


@role_required('user')
def get_home(request):
    user_id = request.session.get('user_id')
    try:
        flashcard = Flashcard.objects.get(user_id=user_id)
    except Flashcard.DoesNotExist:
        return redirect('users:login_form')
    set = (
        FlashcardSet.objects
        .filter(flashcard=flashcard, is_deleted=False)
        .prefetch_related('flashcarditem_set')
    )
    conext = {
        'allSet': set,
        'flashcard':flashcard,
    }
    return render(request, 'flashcards/home.html',conext)

# tạo set id
def generate_set_id():
    last_set = FlashcardSet.objects.order_by('-set_id').first()
    if not last_set:
        return "SET0001"
    number = int(last_set.set_id[3:]) + 1
    return f"SET{number:04d}"

@role_required('user')
def add_set(request, flashcard_id):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid method"}, status=400)
    try:
        fc = Flashcard.objects.get(flashcard_id=flashcard_id)
        set = FlashcardSet.objects.create(
            set_id = generate_set_id(),
            flashcard = fc,
            title = request.POST.get('title','').strip()
        )
        return JsonResponse ({
            'set_id': set.set_id,
            "title": set.title
        })
    except Exception as e:
        # Nếu lỗi 500 xảy ra (ví dụ: flashcard_id không tồn tại), trả về lỗi 400
        print(f"Lỗi khi tạo set: {e}") 
        return JsonResponse({"error": "Failed to create set or invalid Flashcard ID."}, status=400)
    
@role_required('user')
def get_card(request, setID):
    if request.method != 'GET':
        return JsonResponse({"error": "Invalid method"}, status=400)

    try:
        set = FlashcardSet.objects.get(set_id=setID)
    except FlashcardSet.DoesNotExist:
        return JsonResponse({"error": "Set not found"}, status=404)

    cards = FlashcardItem.objects.filter(set= set, is_deleted = False)
    data = [
        model_to_dict(card, fields=['card_id', 'question', 'answer', 'set']) 
        for card in cards
    ]
    
    return JsonResponse(data, safe=False)


def generate_card_id():
    last_card = FlashcardItem.objects.order_by('-card_id').first()
    if not last_card:
        return "CARD0001"
    number = int(last_card.card_id[4:]) + 1
    return f"CARD{number:04d}"

@role_required('user')
def add_card(request,setID):
    if request.method !="POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    
    question_data = request.POST.get('question', '').strip()
    answer_data = request.POST.get('answer', '').strip()

    if not question_data or not answer_data:
        return JsonResponse({"error": "Question and answer fields cannot be empty."}, status=400)
    try:
        set = FlashcardSet.objects.get(set_id=setID)
    except FlashcardSet.DoesNotExist:
        return JsonResponse({"error": "Invalid set ID"}, status=400)
    
    newCard = FlashcardItem.objects.create(
        set =set,
        question=question_data,
        answer=answer_data,
        card_id=generate_card_id()
    )

    return JsonResponse({
            "success": True,
            "message": "Card added successfully.",
            "card": model_to_dict(newCard, fields=['card_id', 'question', 'answer', 'set_id'])
        }, status=201)

@role_required('user')
def edit_card(request,cardID):
    if request.method !="POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    
    question_data = request.POST.get('question', '').strip()
    answer_data = request.POST.get('answer', '').strip()

    if not question_data or not answer_data:
        return JsonResponse({"error": "Question and answer fields cannot be empty."}, status=400)
    try:
        Card = FlashcardItem.objects.get(card_id=cardID)
    except FlashcardItem.DoesNotExist:
        return JsonResponse({"error": "Invalid card ID"}, status=400)

    Card.answer = answer_data
    Card.question = question_data
    Card.save()

    return JsonResponse({
            "success": True,
            "message": "Card updated successfully.",
            # Trả về Set ID của Card để phía Client có thể reload Set đó
            "set_id": Card.set.set_id, 
            "card": model_to_dict(Card, fields=['card_id', 'question', 'answer'])
        }, status=200) # ✅ Dùng 200 OK

@role_required('user')
def study_flashcard_mode(request, set_id):
    # 1. Lấy thông tin Set
    set_instance = get_object_or_404(FlashcardSet, set_id=set_id)
    
    # 2. Lấy tất cả flashcards trong set
    flashcards_queryset = FlashcardItem.objects.filter(set=set_instance)
    
    
    # 3. Tính learned_count đúng cách
    learned_count = flashcards_queryset.filter(learned=True).count()

    # if not flashcards_queryset:
    #     return render :
    
    # 4. Chuyển cards sang dạng list để dễ dàng truyền qua context
    flashcards_list = list(flashcards_queryset.values(
        'card_id', 
        'question', 
        'answer', 
        'learned'
    ))

    # 5. Render template học với dữ liệu
    context = {
        'flashcards': flashcards_list,
        'total_cards': len(flashcards_list),
        'learned_count': learned_count,  # Đây phải là số, không phải QuerySet
        'set_title': set_instance.title,
        'home_url': reverse('flashcards:home'),
    }
    
    return render(request, 'flashcards/flashcard_study_mode.html', context)

import traceback
from django.db import IntegrityError

@csrf_exempt
@require_POST
@role_required('user')
def toggle_learned_status(request, card_id):
    try:
        # Log request info
        print("=" * 50)
        print(f"Toggle learned status for card: {card_id}")
        print(f"User: {request.user} (authenticated: {request.user.is_authenticated})")
        print(f"Request body: {request.body}")
        
        # Parse JSON
        try:
            data = json.loads(request.body)
            print(f"Parsed data: {data}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'Invalid JSON: {str(e)}'
            }, status=400)
        
        # Get card
        try:
            card = FlashcardItem.objects.get(card_id=card_id)
            print(f"Card found: {card.question[:50]}...")
            print(f"Current learned: {card.learned}")
        except FlashcardItem.DoesNotExist:
            print(f"Card not found: {card_id}")
            return JsonResponse({
                'success': False, 
                'error': 'Card not found'
            }, status=404)
        
        # Update learned status
        learned_value = data.get('learned')
        if learned_value is None:
            learned_value = not card.learned  # Toggle if not provided
        
        # Convert to boolean
        if isinstance(learned_value, str):
            learned_value = learned_value.lower() in ('true', '1', 'yes', 'on')
        
        card.learned = bool(learned_value)
        card.save()
        print(f"New learned status saved: {card.learned}")
        
        # Update FlashcardProgress if user is authenticated
        if request.user.is_authenticated:
            try:
                progress, created = FlashcardProgress.objects.get_or_create(
                    card=card,
                    user=request.user,
                    defaults={
                        'status': 'known' if card.learned else 'unknown',
                        'last_reviewed': timezone.now()
                    }
                )
                
                print(f"Progress {'created' if created else 'updated'}")
                
                if not created:
                    progress.status = 'known' if card.learned else 'unknown'
                    progress.last_reviewed = timezone.now()
                    progress.save()
                    print(f"Progress status updated to: {progress.status}")
                
            except IntegrityError as e:
                print(f"Integrity error: {e}")
                # Try update instead
                try:
                    progress = FlashcardProgress.objects.get(card=card, user=request.user)
                    progress.status = 'known' if card.learned else 'unknown'
                    progress.last_reviewed = timezone.now()
                    progress.save()
                    print(f"Progress updated after integrity error")
                except FlashcardProgress.DoesNotExist:
                    print(f"Progress record does not exist")
            except Exception as e:
                print(f"Error updating progress: {e}")
                print(traceback.format_exc())
        else:
            print("User not authenticated, skipping FlashcardProgress update")
        
        print("=" * 50)
        
        return JsonResponse({
            'success': True, 
            'learned': card.learned,
            'card_id': card.card_id,
            'user_authenticated': request.user.is_authenticated
        })
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }, status=500)
    

@role_required('user')
def soft_delete_set(request,setID):
    set = FlashcardSet.objects.get(set_id=setID)
    set.is_deleted = True
    set.save()
    return JsonResponse({"success": True, "message": "Xoá thành công"})

@require_POST
@csrf_exempt
@role_required('user')
def soft_delete_card(request, cardID):
    print(f"Testing delete for card: {cardID}")
    print(f"User authenticated: {request.user.is_authenticated}")
    try:
        card = FlashcardItem.objects.get(card_id=cardID)
        card.is_deleted = True
        card.save()
        return JsonResponse({
            "success": True, 
            "message": "Card deleted successfully"
        })
        
    except FlashcardItem.DoesNotExist:
        return JsonResponse({
            "success": False, 
            "error": "Card not found or you don't have permission"
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)
    

@require_POST
@csrf_exempt
@role_required('user')
def edit_set(request, setID):
    try:
        if not request.body:
            return JsonResponse(
                {"success": False, "error": "Empty request body"},
                status=400
            )

        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400
            )

        title = data.get("title", "").strip()

        flashcard_set = FlashcardSet.objects.get(set_id=setID)

        if title == "":
            flashcard_set.is_deleted = True
            flashcard_set.save()
            return JsonResponse({
                "success": True,
                "deleted": True,
                "message": "Set deleted"
            })

        flashcard_set.title = title
        flashcard_set.save()
        return JsonResponse({
            "success": True,
            "title": flashcard_set.title,
            "message": "Set updated"
        })

    except FlashcardSet.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Set not found"},
            status=404
        )

def generate_progress_id():
    """
    Tạo progress_id tự động: PRG0001, PRG0002, ...
    """
    # Lấy progress cuối cùng
    last_progress = FlashcardProgress.objects.order_by('-progress_id').first()
    
    if not last_progress:
        return "PRG0001"
    
    try:
        # Lấy số từ progress_id (bỏ 3 ký tự đầu "PRG")
        last_number = int(last_progress.progress_id[3:])
        new_number = last_number + 1
        return f"PRG{new_number:04d}"  # 4 chữ số, thêm số 0 ở đầu
    except (ValueError, IndexError):
        # Nếu có lỗi, trả về mặc định
        return "PRG0001"

# views.py - thêm view sau
@role_required('user')
def essay_mode_view(request, set_id):
    """
    Chế độ tự luận: hiển thị câu hỏi flashcard, người dùng nhập câu trả lời
    """
    
    # Lấy set
    flashcard_set = get_object_or_404(FlashcardSet, set_id=set_id)
    
    # Lấy tất cả flashcard trong set
    flashcards = FlashcardItem.objects.filter(
        set=flashcard_set,
        is_deleted=False
    )
    
    if request.method == 'POST':
        # Lấy user từ session
        user_id = request.session.get('user_id')
        from django.contrib.auth import get_user_model
        
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return HttpResponse('<script>alert("Tài khoản không tồn tại."); window.location.href="/users/login/";</script>')
        
        correct_count = 0
        total_questions = flashcards.count()
        
        for flashcard in flashcards:
            answer_key = f'answer_{flashcard.card_id}'
            user_answer = request.POST.get(answer_key, '').strip().lower()
            correct_answer = flashcard.answer.strip().lower()
            
            # So sánh câu trả lời
            is_correct = user_answer == correct_answer
            
            if is_correct:
                correct_count += 1
                
                # SỬA: Dùng update_or_create
                try:
                    # Thử lấy progress hiện có
                    progress = FlashcardProgress.objects.get(
                        card=flashcard,
                        user=user
                    )
                    # Nếu tồn tại, cập nhật
                    progress.status = 'known'
                    progress.last_reviewed = timezone.now()
                    progress.save()
                except FlashcardProgress.DoesNotExist:
                    # Nếu không tồn tại, tạo mới
                    FlashcardProgress.objects.create(
                        progress_id=generate_progress_id(),
                        card=flashcard,
                        user=user,
                        status='known',
                        last_reviewed=timezone.now()
                    )
                
                # Cập nhật learned status
                flashcard.learned = True
                flashcard.save()
        
        # Tính điểm
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        from datetime import datetime
        request.session['essay_results'] = {
            'set_id': set_id,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'score_percentage': score_percentage,
            'flashcard_set_title': flashcard_set.title,
            'submitted_at': datetime.now().strftime('%H:%M %d/%m/%Y'),  # Thêm timestamp
            'user_id': user_id  # Thêm user_id để kiểm tra
        }

        # Xóa session cũ để tránh cache
        request.session.modified = True
        
        # Redirect đến trang kết quả
        return redirect('flashcards:essay_results', set_id=set_id)
    
    # GET request: hiển thị form
    context = {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
        'total_count': flashcards.count(),
    }
    
    return render(request, 'flashcards/essay_mode.html', context)

@role_required('user')
def essay_results_view(request, set_id):
    """
    Hiển thị kết quả bài làm tự luận
    """
    flashcard_set = get_object_or_404(FlashcardSet, set_id=set_id)
    
    # Lấy user từ session (giống như trong essay_mode_view)
    user_id = request.session.get('user_id')
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return HttpResponse('<script>alert("Tài khoản không tồn tại."); window.location.href="/users/login/";</script>')
    
    # Lấy progress của user cho set này
    flashcards = FlashcardItem.objects.filter(
        set=flashcard_set,
        is_deleted=False
    )
    
    progress_list = []
    for flashcard in flashcards:
        try:
            progress = FlashcardProgress.objects.get(
                card=flashcard,
                user=user  # Sử dụng user từ session
            )
            progress_list.append({
                'flashcard': flashcard,
                'progress': progress,
                'status': progress.status
            })
        except FlashcardProgress.DoesNotExist:
            progress_list.append({
                'flashcard': flashcard,
                'progress': None,
                'status': 'unknown'
            })
    
    # Lấy kết quả từ session để hiển thị số câu đúng
    essay_results = request.session.get('essay_results', {})
    correct_count = essay_results.get('correct_count', 0)
    total_questions = essay_results.get('total_questions', flashcards.count())
    score_percentage = essay_results.get('score_percentage', 0)
    
    # Tính thống kê từ progress
    known_count = sum(1 for p in progress_list if p['status'] == 'known')
    total_count = len(progress_list)
    
    return render(request, 'flashcards/essay_results.html', {
        'flashcard_set': flashcard_set,
        'progress_list': progress_list,
        'known_count': known_count,
        'correct_count': correct_count,  # Thêm vào context
        'total_count': total_count,
        'total_questions': total_questions,
        'score_percentage': score_percentage,
        'percentage': (known_count / total_count * 100) if total_count > 0 else 0,
        'essay_results': essay_results,  # Truyền toàn bộ kết quả
    })


# View để xem chi tiết từng câu trả lời
@role_required('user')
def review_essay_answers(request, set_id):
    """
    Xem lại câu trả lời tự luận (nếu lưu lại)
    """
    flashcard_set = get_object_or_404(FlashcardSet, set_id=set_id)
    
    # Trong thực tế, bạn có thể muốn lưu câu trả lời của user
    # Tạm thời hiển thị flashcard và đáp án
    flashcards = FlashcardItem.objects.filter(
        set=flashcard_set,
        is_deleted=False
    )
    
    return render(request, 'flashcards/review_essay.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
    })