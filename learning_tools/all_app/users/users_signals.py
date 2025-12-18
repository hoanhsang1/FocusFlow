from django.db.models.signals import post_save
from django.dispatch import receiver
# from to_do_list.to_do_list_models import ToDoList
# from habit.habit_models import Habit
# from calendar_app.calendar_models import Calendar
# from flashcards.flashcards_models import Flashcard
# from pomodoro.pomodoro_models import Pomodoro
from .users_models import User
import uuid
from django.apps import apps

def gen_id():
    return str(uuid.uuid4())[:10]


@receiver(post_save, sender=User)
def create_user_related_data(sender, instance, created, **kwargs):
    if created:
        try:
            # Lấy models thông qua apps.get_model() thay vì import trực tiếp
            ToDoList = apps.get_model('all_app.to_do_list', 'ToDoList')
            Habit = apps.get_model('all_app.habit', 'Habit')
            Calendar = apps.get_model('all_app.calendar_app', 'Calendar')
            Flashcard = apps.get_model('all_app.flashcards', 'Flashcard')
            Pomodoro = apps.get_model('all_app.pomodoro', 'Pomodoro')

            # Tạo ToDoList mặc định
            ToDoList.objects.create(
                todolist_id=gen_id(),
                user=instance
            )

            # Tạo HabitList mặc định
            Habit.objects.create(
                habitlist_id=gen_id(),
                user=instance
            )

            # Tạo Calendar mặc định
            Calendar.objects.create(
                calendar_id=gen_id(),
                user=instance
            )

            # Tạo Flashcard mặc định
            Flashcard.objects.create(
                flashcard_id=gen_id(),
                user=instance
            )

            # Tạo Pomodoro mặc định
            Pomodoro.objects.create(
                pomodoro_id=gen_id(),
                user=instance
            )
        except Exception as e:
            print(f"Signal error: {e}")  # In lỗi nếu có