from django.db import models
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]

# ===========================
# FLASHCARDS
# ===========================

class Flashcard(models.Model):
    flashcard_id = models.CharField(primary_key=True, default=generate_id, max_length=10)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Flashcard'
        managed = False

    def __str__(self):
        return self.flashcard_id


class FlashcardSet(models.Model):
    set_id = models.CharField(primary_key=True, max_length=10)
    flashcard = models.ForeignKey("flashcards.Flashcard", on_delete=models.CASCADE, db_column='flashcard_id')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'FlashcardSet'
        managed = False

    def __str__(self):
        return self.title


class FlashcardItem(models.Model):
    card_id = models.CharField(primary_key=True, max_length=10)
    set = models.ForeignKey("flashcards.FlashcardSet", on_delete=models.CASCADE, db_column='set_id')
    question = models.CharField(max_length=150)
    answer = models.CharField(max_length=150)
    learned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'FlashcardItem'
        managed = False

    def __str__(self):
        return self.card_id


class FlashcardProgress(models.Model):
    progress_id = models.CharField(primary_key=True, max_length=10)
    card = models.ForeignKey("flashcards.FlashcardItem", on_delete=models.CASCADE, db_column='card_id')
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column='user_id')
    status = models.CharField(max_length=32, default='unknown')
    last_reviewed = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'FlashcardProgress'
        managed = False
        unique_together = ('card', 'user')

    def __str__(self):
        return self.progress_id
