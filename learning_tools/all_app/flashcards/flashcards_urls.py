from django.contrib import admin
from django.urls import path
from . import flashcards_views as views
app_name = 'flashcards'

urlpatterns = [
    path('home/',views.get_home, name='home'),
    path('home/add_set/<str:flashcard_id>',views.add_set, name='add_set'),
    path('home/get_card/<str:setID>',views.get_card, name='get_card'),
    path('home/add_card/<str:setID>',views.add_card, name='add_card'),
    path('home/edit_card/<str:cardID>',views.edit_card, name='edit_card'),
    path('home/edit_set/<str:setID>',views.edit_set, name='edit_set'),
    path('home/delete_card/<str:cardID>',views.soft_delete_card, name='delete_card'),
    path('flashcard_learn/<str:card_id>/toggle-learned/', views.toggle_learned_status, name='toggle_learned'),
    path('home/study/<str:set_id>/flashcard', views.study_flashcard_mode, name='study_flashcard'),
]