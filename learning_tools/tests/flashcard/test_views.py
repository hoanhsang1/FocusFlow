from unittest import mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock
import sys

print("=" * 60)
print("STARTING TEST FILE: test_views.py")
print("=" * 60)

try:
    from all_app.flashcards.flashcards_models import *  # ✅ ĐÚNG
    HAS_FLASHCARD_MODEL = True
    print("[IMPORT] ✓ Successfully imported custom FLASHCARD model")
except ImportError:
    HAS_FLASHCARD_MODEL = False
    print("[IMPORT] ⚠ Could not import custom FLASHCARD model")

try:
    from all_app.users.users_models import User  # ✅ ĐÚNG
    HAS_USER_MODEL = True
    print("[IMPORT] ✓ Successfully imported custom User model")
except ImportError:
    HAS_USER_MODEL = False
    print("[IMPORT] ⚠ Could not import custom User model")

try:
    from all_app.users.check_login_role import *  # ✅ ĐÚNG
    HAS_USER_MODEL = True
    print("[IMPORT] ✓ Successfully imported check_login_role")
except ImportError:
    HAS_USER_MODEL = False
    print("[IMPORT] ⚠ Could not import check_login_role")

# CLASS CHUNG CHO TẤT CẢ TESTS
class UserTestData(TestCase):
    def setUp(self):
        print(f"\n[SETUP] {self.__class__.__name__}: Setting up test data")
        
        # Tạo user và login
        self.client = Client()
        print("  [INFO] Created test client")
        
        self.user = User.objects.create(
            username='testuser',
            password='testpass123'
        )
        print(f"  [INFO] Created test user: {self.user.username}")
        
        # Lưu vào session (giống đăng nhập)
        session = self.client.session
        session['user_id'] = self.user.user_id
        session['role'] = 'user'
        session.save()
        print(f"  [INFO] Set session: user_id={session['user_id']}, role={session['role']}")
        
        # Tạo Flashcard cho user này
        self.flashcard = Flashcard.objects.create(
            flashcard_id='FC001',
            user=self.user
        )
        print(f"  [INFO] Created flashcard: {self.flashcard.flashcard_id}")
        
        print(f"  [DONE] {self.__class__.__name__} setup completed")
    
    def tearDown(self):
        print(f"\n[TEARDOWN] {self.__class__.__name__}: Cleaning up")
        super().tearDown()

# TEST ĐĂNG NHẬP
class AuthenticationTests(UserTestData):
    def test_home_needs_login(self):
        print(f"\n[TEST] {self._testMethodName}: Testing home page requires login")
        
        # Xóa session = chưa login
        self.client.session.flush()
        print("  [ACTION] Cleared user session (simulating not logged in)")
        
        response = self.client.get(reverse('flashcards:home'))
        print(f"  [RESPONSE] Status: {response.status_code}, URL: {response.url}")
        
        # Phải chuyển về trang login
        self.assertEqual(response.status_code, 302)
        print("  [CHECK] ✓ Status code is 302 (redirect)")
        
        self.assertTrue('/login' in response.url)
        print(f"  [CHECK] ✓ Redirects to login page: {response.url}")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_home_with_wrong_role(self):
        print(f"\n[TEST] {self._testMethodName}: Testing home page with wrong role")
        
        # Đổi role thành admin (sai)
        session = self.client.session
        session['role'] = 'admin'
        session.save()
        print(f"  [ACTION] Changed role to: {session['role']}")
        
        response = self.client.get(reverse('flashcards:home'))
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        # Phải báo lỗi không có quyền
        self.assertEqual(response.status_code, 403)
        print("  [CHECK] ✓ Status code is 403 (forbidden)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_home_with_no_flashcard(self):
        print(f"\n[TEST] {self._testMethodName}: Testing home page when user has no flashcard")
        
        # Xóa flashcard của user
        Flashcard.objects.filter(user=self.user).delete()
        print("  [ACTION] Deleted user's flashcard")
        
        response = self.client.get(reverse('flashcards:home'))
        print(f"  [RESPONSE] Status: {response.status_code}, URL: {response.url}")
        
        # Phải chuyển về login (theo code mới)
        self.assertEqual(response.status_code, 302)
        print("  [CHECK] ✓ Status code is 302 (redirect)")
        
        self.assertTrue('/login' in response.url)
        print(f"  [CHECK] ✓ Redirects to login page: {response.url}")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_home_page_works(self):
        print(f"\n[TEST] {self._testMethodName}: Testing home page access when logged in")
        
        response = self.client.get(reverse('flashcards:home'))
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        # Khi đã login và có flashcard thì vào được
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")

# TEST QUẢN LÝ SET
class SetManagementTests(UserTestData):
    def setUp(self):
        super().setUp()
        print(f"\n[SETUP] {self.__class__.__name__}: Additional setup for set management tests")
        
        # Tạo set test
        self.test_set = FlashcardSet.objects.create(
            set_id='SET001',
            flashcard=self.flashcard,
            title='Test Set'
        )
        print(f"  [INFO] Created test set: {self.test_set.set_id} - '{self.test_set.title}'")
        
        print(f"  [DONE] {self.__class__.__name__} setup completed")
    
    def test_create_set_success(self):
        print(f"\n[TEST] {self._testMethodName}: Testing successful set creation")
        
        url = reverse('flashcards:add_set', args=['FC001'])
        print(f"  [URL] POST to: {url}")
        
        data = {'title': 'New Flashcard Set'}
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        # Kiểm tra kết quả
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['title'], 'New Flashcard Set')
        print("  [CHECK] ✓ Title matches in response")
        
        self.assertTrue('set_id' in response_data)
        print(f"  [CHECK] ✓ Set ID generated: {response_data['set_id']}")
        
        # Kiểm tra trong database
        self.assertEqual(FlashcardSet.objects.count(), 2)
        print(f"  [CHECK] ✓ Database has {FlashcardSet.objects.count()} sets (expected 2)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_create_set_with_invalid_flashcard(self):
        print(f"\n[TEST] {self._testMethodName}: Testing set creation with invalid flashcard ID")
        
        # Flashcard ID không tồn tại
        url = reverse('flashcards:add_set', args=['INVALID'])
        print(f"  [URL] POST to: {url} (invalid flashcard ID)")
        
        data = {'title': 'Test'}
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("  [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Failed to create set or invalid Flashcard ID.')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_edit_set_title(self):
        print(f"\n[TEST] {self._testMethodName}: Testing set title update")
        
        url = reverse('flashcards:edit_set', args=['SET001'])
        print(f"  [URL] POST to: {url}")
        
        data = json.dumps({'title': 'Updated Title'})
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data, content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue(response_data['success'])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertEqual(response_data['title'], 'Updated Title')
        print(f"  [CHECK] ✓ Title updated to: {response_data['title']}")
        
        # Kiểm tra database
        self.test_set.refresh_from_db()
        print(f"  [DATABASE] Set title after refresh: '{self.test_set.title}'")
        
        self.assertEqual(self.test_set.title, 'Updated Title')
        print("  [CHECK] ✓ Database updated correctly")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_delete_set_with_empty_title(self):
        print(f"\n[TEST] {self._testMethodName}: Testing set deletion with empty title")
        
        url = reverse('flashcards:edit_set', args=['SET001'])
        print(f"  [URL] POST to: {url}")
        
        data = json.dumps({'title': ''})  # Title rỗng = xóa
        print(f"  [DATA] Request data: {data} (empty title for deletion)")
        
        response = self.client.post(url, data, content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue(response_data['success'])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertTrue(response_data['deleted'])
        print("  [CHECK] ✓ Deleted flag is True")
        
        # Kiểm tra soft delete
        self.test_set.refresh_from_db()
        print(f"  [DATABASE] Set is_deleted after refresh: {self.test_set.is_deleted}")
        
        self.assertTrue(self.test_set.is_deleted)
        print("  [CHECK] ✓ Set marked as deleted in database")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_edit_set_not_found(self):
        print(f"\n[TEST] {self._testMethodName}: Testing edit non-existent set")
        
        url = reverse('flashcards:edit_set', args=['INVALID'])
        print(f"  [URL] POST to: {url} (invalid set ID)")
        
        data = json.dumps({'title': 'Test'})
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data, content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 404)
        print("  [CHECK] ✓ Status code is 404 (not found)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Set not found')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_edit_set_invalid_json(self):
        print(f"\n[TEST] {self._testMethodName}: Testing edit set with invalid JSON")
        
        url = reverse('flashcards:edit_set', args=['SET001'])
        print(f"  [URL] POST to: {url}")
        
        # Gửi JSON sai
        response = self.client.post(url, 'invalid json', content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("  [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Invalid JSON')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")

# TEST QUẢN LÝ CARD
class CardManagementTests(UserTestData):
    def setUp(self):
        super().setUp()
        print(f"\n[SETUP] {self.__class__.__name__}: Additional setup for card management tests")
        
        # Tạo set và card test
        self.test_set = FlashcardSet.objects.create(
            set_id='SET001',
            flashcard=self.flashcard,
            title='Test Set'
        )
        print(f"  [INFO] Created test set: {self.test_set.set_id}")
        
        self.test_card = FlashcardItem.objects.create(
            card_id='CARD001',
            set=self.test_set,
            question='Question 1',
            answer='Answer 1'
        )
        print(f"  [INFO] Created test card: {self.test_card.card_id} - '{self.test_card.question}'")
        
        print(f"  [DONE] {self.__class__.__name__} setup completed")
    
    def test_add_card_success(self):
        print(f"\n[TEST] {self._testMethodName}: Testing successful card creation")
        
        url = reverse('flashcards:add_card', args=['SET001'])
        print(f"  [URL] POST to: {url}")
        
        data = {
            'question': 'What is Python?',
            'answer': 'Programming language'
        }
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 201)
        print("  [CHECK] ✓ Status code is 201 (created)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue(response_data['success'])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertEqual(response_data['message'], 'Card added successfully.')
        print("  [CHECK] ✓ Message is correct")
        
        # Kiểm tra database
        self.assertEqual(FlashcardItem.objects.count(), 2)
        print(f"  [CHECK] ✓ Database has {FlashcardItem.objects.count()} cards (expected 2)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_add_card_empty_fields(self):
        print(f"\n[TEST] {self._testMethodName}: Testing card creation with empty fields")
        
        url = reverse('flashcards:add_card', args=['SET001'])
        print(f"  [URL] POST to: {url}")
        
        # Test 1: Question rỗng
        print("  [TEST CASE 1] Empty question")
        data = {'question': '', 'answer': 'Some answer'}
        print(f"    [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"    [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("    [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"    [DATA] Response data: {response_data}")
        
        # Test 2: Answer rỗng
        print("\n  [TEST CASE 2] Empty answer")
        data = {'question': 'Some question', 'answer': ''}
        print(f"    [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"    [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("    [CHECK] ✓ Status code is 400 (bad request)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_add_card_invalid_set(self):
        print(f"\n[TEST] {self._testMethodName}: Testing card creation with invalid set ID")
        
        url = reverse('flashcards:add_card', args=['INVALID'])
        print(f"  [URL] POST to: {url} (invalid set ID)")
        
        data = {'question': 'Test', 'answer': 'Test'}
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("  [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Invalid set ID')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_edit_card_success(self):
        print(f"\n[TEST] {self._testMethodName}: Testing successful card edit")
        
        url = reverse('flashcards:edit_card', args=['CARD001'])
        print(f"  [URL] POST to: {url}")
        
        data = {
            'question': 'Updated Question',
            'answer': 'Updated Answer'
        }
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue(response_data['success'])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertEqual(response_data['message'], 'Card updated successfully.')
        print("  [CHECK] ✓ Message is correct")
        
        # Kiểm tra database
        self.test_card.refresh_from_db()
        print(f"  [DATABASE] Card after update:")
        print(f"    - Question: '{self.test_card.question}'")
        print(f"    - Answer: '{self.test_card.answer}'")
        
        self.assertEqual(self.test_card.question, 'Updated Question')
        print("  [CHECK] ✓ Question updated in database")
        
        self.assertEqual(self.test_card.answer, 'Updated Answer')
        print("  [CHECK] ✓ Answer updated in database")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_edit_card_not_found(self):
        print(f"\n[TEST] {self._testMethodName}: Testing edit non-existent card")
        
        url = reverse('flashcards:edit_card', args=['INVALID'])
        print(f"  [URL] POST to: {url} (invalid card ID)")
        
        data = {'question': 'Test', 'answer': 'Test'}
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("  [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Invalid card ID')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_delete_card(self):
        print(f"\n[TEST] {self._testMethodName}: Testing card deletion")
        
        url = reverse('flashcards:delete_card', args=['CARD001'])
        print(f"  [URL] POST to: {url}")
        
        response = self.client.post(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue(response_data['success'])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertEqual(response_data['message'], 'Card deleted successfully')
        print("  [CHECK] ✓ Message is correct")
        
        # Kiểm tra soft delete
        self.test_card.refresh_from_db()
        print(f"  [DATABASE] Card is_deleted after refresh: {self.test_card.is_deleted}")
        
        self.assertTrue(self.test_card.is_deleted)
        print("  [CHECK] ✓ Card marked as deleted in database")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_delete_card_not_found(self):
        print(f"\n[TEST] {self._testMethodName}: Testing delete non-existent card")
        
        url = reverse('flashcards:delete_card', args=['INVALID'])
        print(f"  [URL] POST to: {url} (invalid card ID)")
        
        response = self.client.post(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 404)
        print("  [CHECK] ✓ Status code is 404 (not found)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Card not found or you don\'t have permission')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_get_cards_from_set(self):
        print(f"\n[TEST] {self._testMethodName}: Testing get cards from set")
        
        # Tạo thêm 1 card nữa
        FlashcardItem.objects.create(
            card_id='CARD002',
            set=self.test_set,
            question='Question 2',
            answer='Answer 2'
        )
        print("  [INFO] Created additional test card: CARD002")
        
        url = reverse('flashcards:get_card', args=['SET001'])
        print(f"  [URL] GET to: {url}")
        
        response = self.client.get(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Retrieved {len(response_data)} cards")
        
        self.assertEqual(len(response_data), 2)
        print("  [CHECK] ✓ Got 2 cards (expected 2)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_get_cards_set_not_found(self):
        print(f"\n[TEST] {self._testMethodName}: Testing get cards from non-existent set")
        
        url = reverse('flashcards:get_card', args=['INVALID'])
        print(f"  [URL] GET to: {url} (invalid set ID)")
        
        response = self.client.get(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 404)
        print("  [CHECK] ✓ Status code is 404 (not found)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Set not found')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_get_cards_wrong_method(self):
        print(f"\n[TEST] {self._testMethodName}: Testing wrong HTTP method for get_cards")
        
        url = reverse('flashcards:get_card', args=['SET001'])
        print(f"  [URL] POST to: {url} (should be GET)")
        
        # Dùng POST thay vì GET
        response = self.client.post(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("  [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Invalid method')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")

# TEST CHẾ ĐỘ HỌC
class StudyModeTests(UserTestData):
    def setUp(self):
        super().setUp()
        print(f"\n[SETUP] {self.__class__.__name__}: Additional setup for study mode tests")
        
        # Tạo set với cards
        self.test_set = FlashcardSet.objects.create(
            set_id='SET001',
            flashcard=self.flashcard,
            title='Study Set'
        )
        print(f"  [INFO] Created study set: {self.test_set.set_id} - '{self.test_set.title}'")
        
        # Card chưa học
        FlashcardItem.objects.create(
            card_id='CARD001',
            set=self.test_set,
            question='Q1',
            answer='A1',
            learned=False
        )
        print("  [INFO] Created card 1: CARD001 (not learned)")
        
        # Card đã học
        FlashcardItem.objects.create(
            card_id='CARD002',
            set=self.test_set,
            question='Q2',
            answer='A2',
            learned=True
        )
        print("  [INFO] Created card 2: CARD002 (learned)")
        
        print(f"  [DONE] {self.__class__.__name__} setup completed")
    
    def test_study_page(self):
        print(f"\n[TEST] {self._testMethodName}: Testing study page access")
        
        url = reverse('flashcards:study_flashcard', args=['SET001'])
        print(f"  [URL] GET to: {url}")
        
        response = self.client.get(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        # Kiểm tra context
        context = response.context
        print(f"  [CONTEXT] Context data:")
        print(f"    - total_cards: {context['total_cards']}")
        print(f"    - learned_count: {context['learned_count']}")
        print(f"    - set_title: '{context['set_title']}'")
        
        self.assertEqual(context['total_cards'], 2)
        print("  [CHECK] ✓ Total cards: 2 (expected 2)")
        
        self.assertEqual(context['learned_count'], 1)
        print("  [CHECK] ✓ Learned count: 1 (expected 1)")
        
        self.assertEqual(context['set_title'], 'Study Set')
        print("  [CHECK] ✓ Set title is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_study_page_set_not_found(self):
        print(f"\n[TEST] {self._testMethodName}: Testing study page with non-existent set")
        
        url = reverse('flashcards:study_flashcard', args=['INVALID'])
        print(f"  [URL] GET to: {url} (invalid set ID)")
        
        response = self.client.get(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 404)
        print("  [CHECK] ✓ Status code is 404 (not found)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_toggle_learned_status(self):
        print(f"\n[TEST] {self._testMethodName}: Testing toggle learned status")
        
        url = reverse('flashcards:toggle_learned', args=['CARD001'])
        print(f"  [URL] POST to: {url}")
        
        data = json.dumps({'learned': True})
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data, content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue(response_data['success'])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertTrue(response_data['learned'])
        print("  [CHECK] ✓ Learned status is True")
        
        # Kiểm tra database
        card = FlashcardItem.objects.get(card_id='CARD001')
        print(f"  [DATABASE] Card learned after toggle: {card.learned}")
        
        self.assertTrue(card.learned)
        print("  [CHECK] ✓ Card marked as learned in database")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_toggle_learned_card_not_found(self):
        print(f"\n[TEST] {self._testMethodName}: Testing toggle learned for non-existent card")
        
        url = reverse('flashcards:toggle_learned', args=['INVALID'])
        print(f"  [URL] POST to: {url} (invalid card ID)")
        
        data = json.dumps({'learned': True})
        print(f"  [DATA] Request data: {data}")
        
        response = self.client.post(url, data, content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 404)
        print("  [CHECK] ✓ Status code is 404 (not found)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertEqual(response_data['error'], 'Card not found')
        print("  [CHECK] ✓ Error message is correct")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_toggle_learned_invalid_json(self):
        print(f"\n[TEST] {self._testMethodName}: Testing toggle learned with invalid JSON")
        
        url = reverse('flashcards:toggle_learned', args=['CARD001'])
        print(f"  [URL] POST to: {url}")
        
        # Gửi JSON sai
        response = self.client.post(url, 'invalid json', content_type='application/json')
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 400)
        print("  [CHECK] ✓ Status code is 400 (bad request)")
        
        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")
        
        self.assertTrue('error' in response_data)
        print("  [CHECK] ✓ Error key exists in response")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")

# TEST TỐC ĐỘ (PERFORMANCE)
class PerformanceTests(UserTestData):
    def test_home_with_many_sets(self):
        print(f"\n[TEST] {self._testMethodName}: Testing home page performance with many sets")
        
        # Tạo 20 sets
        print("  [ACTION] Creating 20 test sets...")
        for i in range(20):
            FlashcardSet.objects.create(
                set_id=f'SET{str(i+1).zfill(3)}',
                flashcard=self.flashcard,
                title=f'Set {i+1}'
            )
        print("  [INFO] Created 20 sets")
        
        # Test truy cập home
        response = self.client.get(reverse('flashcards:home'))
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_get_cards_with_many_cards(self):
        print(f"\n[TEST] {self._testMethodName}: Testing get cards performance with many cards")
        
        # Tạo set
        test_set = FlashcardSet.objects.create(
            set_id='BIGSET',
            flashcard=self.flashcard,
            title='Big Set'
        )
        print("  [INFO] Created big set: BIGSET")
        
        # Tạo 30 cards
        print("  [ACTION] Creating 30 test cards...")
        for i in range(30):
            FlashcardItem.objects.create(
                card_id=f'CARD{str(i+1).zfill(3)}',
                set=test_set,
                question=f'Question {i+1}',
                answer=f'Answer {i+1}'
            )
        print("  [INFO] Created 30 cards")
        
        # Test lấy cards
        url = reverse('flashcards:get_card', args=['BIGSET'])
        print(f"  [URL] GET to: {url}")
        
        response = self.client.get(url)
        print(f"  [RESPONSE] Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")
        
        response_data = response.json()
        print(f"  [DATA] Retrieved {len(response_data)} cards")
        
        self.assertEqual(len(response_data), 30)
        print("  [CHECK] ✓ Got 30 cards (expected 30)")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")

# TEST THÊM
class AdditionalTests(UserTestData):
    def test_generate_set_id(self):
        print(f"\n[TEST] {self._testMethodName}: Testing generate_set_id function")
        
        # Test khi không có set nào
        FlashcardSet.objects.all().delete()
        print("  [ACTION] Deleted all sets from database")
        
        # Import hàm generate_set_id từ views
        from all_app.flashcards.flashcards_views import generate_set_id
        
        result = generate_set_id()
        print(f"  [RESULT] Generated set ID: {result}")
        
        self.assertEqual(result, 'SET0001')
        print("  [CHECK] ✓ First set ID is SET0001")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_generate_card_id(self):
        print(f"\n[TEST] {self._testMethodName}: Testing generate_card_id function")
        
        # Test khi không có card nào
        FlashcardItem.objects.all().delete()
        print("  [ACTION] Deleted all cards from database")
        
        # Import hàm generate_card_id từ views
        from all_app.flashcards.flashcards_views import generate_card_id
        
        result = generate_card_id()
        print(f"  [RESULT] Generated card ID: {result}")
        
        self.assertEqual(result, 'CARD0001')
        print("  [CHECK] ✓ First card ID is CARD0001")
        
        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")
    
    def test_soft_delete_set_view(self):
        print(f"\n[TEST] {self._testMethodName}: Testing soft delete set view")
        
        test_set = FlashcardSet.objects.create(
            set_id='SET999',
            flashcard=self.flashcard,
            title='Test title'
        )
        print(f"  [INFO] Created test set: SET999 - 'Test title'")

        url = reverse('flashcards:edit_set', args=['SET999'])
        print(f"  [URL] POST to: {url}")

        response = self.client.post(
            url,
            data=json.dumps({"title": ""}),
            content_type="application/json"
        )
        print(f"  [RESPONSE] Status: {response.status_code}")

        self.assertEqual(response.status_code, 200)
        print("  [CHECK] ✓ Status code is 200 (success)")

        response_data = response.json()
        print(f"  [DATA] Response data: {response_data}")

        self.assertTrue(response_data["success"])
        print("  [CHECK] ✓ Success flag is True")
        
        self.assertTrue(response_data["deleted"])
        print("  [CHECK] ✓ Deleted flag is True")
        
        self.assertEqual(response_data["message"], "Set deleted")
        print("  [CHECK] ✓ Message is correct")

        # Kiểm tra DB
        test_set.refresh_from_db()
        print(f"  [DATABASE] Set is_deleted after delete: {test_set.is_deleted}")
        
        self.assertTrue(test_set.is_deleted)
        print("  [CHECK] ✓ Set marked as deleted in database")

        print(f"  [RESULT] ✓ TEST PASSED: {self._testMethodName}")

print("\n" + "="*60)
print("ALL TEST CLASSES DEFINED SUCCESSFULLY")
print("="*60)