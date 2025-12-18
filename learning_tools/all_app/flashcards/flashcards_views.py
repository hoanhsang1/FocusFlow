from datetime import timezone
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from all_app.users.check_login_role import *
from .flashcards_models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.views.decorators.http import require_POST
import json
# Create your views here.

@role_required('user')
def get_home(request):
    user_id = request.session.get('user_id')
    try:
        flashcard = Flashcard.objects.get(user_id=user_id)
    except Flashcard.DoesNotExist:
        return redirect('set+up_todolist')
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

def study_flashcard_mode(request, set_id):
    # 1. Lấy thông tin Set
    set_instance = get_object_or_404(FlashcardSet, set_id=set_id)
    
    # 2. Lấy tất cả flashcards trong set
    flashcards_queryset = FlashcardItem.objects.filter(set=set_instance)
    
    # 3. Tính learned_count đúng cách
    learned_count = flashcards_queryset.filter(learned=True).count()
    
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
    

def soft_delete_set(request,setID):
    set = FlashcardSet.objects.get(set_id=setID)
    set.is_deleted = True
    set.save()
    return JsonResponse({"success": True, "message": "Xoá thành công"})

@require_POST
@csrf_exempt
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
def edit_set(request, setID):
    
    try:
        # Parse JSON từ request body
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                print(f"Parsed JSON data: {data}")
                title = data.get("title", "").strip()
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                # Thử đọc như form data
                title = request.POST.get("title", "").strip()
        else:
            title = request.POST.get("title", "").strip()
        
        print(f"Title: '{title}'")
        
        # Kiểm authentication (tạm bỏ qua để test)
        # if not request.user.is_authenticated:
        #     return JsonResponse({"success": False, "error": "Login required"}, status=401)
        
        
        flashcard_set = FlashcardSet.objects.get(set_id=setID)
        # flashcard_set = FlashcardSet.objects.get(set_id=setID, user=request.user)  # Khi có auth
        
        if title == '':
            # Xóa mềm
            flashcard_set.is_deleted = True
            flashcard_set.save()
            print(f"Set {setID} marked as deleted")
            
            return JsonResponse({
                "success": True, 
                "deleted": True,
                "message": "Set deleted"
            })
        else:
            # Cập nhật title
            flashcard_set.title = title
            flashcard_set.save()
            print(f"Set {setID} title updated to: {title}")
            
            return JsonResponse({
                "success": True, 
                "title": flashcard_set.title,
                "message": "Set updated"
            })
        
    except FlashcardSet.DoesNotExist:
        print(f"Set {setID} not found")
        return JsonResponse({
            "success": False, 
            "error": "Set not found"
        }, status=404)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)