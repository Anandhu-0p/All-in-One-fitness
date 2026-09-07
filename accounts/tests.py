from datetime import date, timedelta
from io import BytesIO

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import PlatformContent, UserProfile
from accounts.utils import ROLE_EXPERT, ROLE_TRAINER, ROLE_USER, assign_role
from chat.models import ChatConversation, ChatMessage
from events.models import Event, EventRegistration
from experts.models import DietPlan, DietPlanMeal, ExpertProfile, FitnessVideo, UserDietAssignment, WellnessTip
from fitness.models import UserWorkoutAssignment, WorkoutExercise, WorkoutPlan
from notifications.models import Feedback, Notification
from payments.models import MembershipPlan, Payment, PaymentAlert
from trainers.models import Attendance, Batch, BatchMembership, TrainerAssignment, TrainerProfile
from users.models import HealthRecord, ProgressRecord

PASSWORD = 'Fitness@123'


def make_user(username, role, **extra):
    email = extra.pop('email', f'{username}@example.com')
    user = User.objects.create_user(username=username, password=PASSWORD, email=email, **extra)
    assign_role(user, role)
    return user


class BaseSetup(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name in (ROLE_TRAINER, ROLE_EXPERT, ROLE_USER):
            Group.objects.get_or_create(name=name)
        cls.admin = User.objects.create_superuser('admin', 'admin@example.com', PASSWORD)
        cls.trainer_user = make_user('trainer', ROLE_TRAINER)
        cls.expert_user = make_user('expert', ROLE_EXPERT)
        cls.user = make_user('user', ROLE_USER)
        cls.other_user = make_user('other', ROLE_USER)

        cls.trainer = TrainerProfile.objects.create(
            user=cls.trainer_user, full_name='Trainer One', email='trainer@example.com', specialization='Strength',
        )
        cls.expert = ExpertProfile.objects.create(
            user=cls.expert_user, full_name='Expert One', email='expert@example.com', specialization='Nutrition',
        )
        UserProfile.objects.get_or_create(user=cls.user, defaults={'full_name': 'User One', 'email': 'user@example.com'})

        today = date.today()
        cls.batch = Batch.objects.create(
            name='Test Batch', start_date=today, end_date=today + timedelta(days=90),
            schedule='Mon/Wed/Fri 6:00 AM', capacity=20, status='Active',
        )
        cls.batch2 = Batch.objects.create(
            name='Test Batch 2', start_date=today, end_date=today + timedelta(days=60), status='Active',
        )
        cls.membership = BatchMembership.objects.create(batch=cls.batch, user=cls.user, status='Active')
        TrainerAssignment.objects.create(batch=cls.batch, trainer=cls.trainer, status='Active')

        cls.workout = WorkoutPlan.objects.create(
            title='Test Workout', goal='Strength', created_by_trainer=cls.trainer, difficulty_level='Beginner',
        )
        WorkoutExercise.objects.create(workout_plan=cls.workout, exercise_name='Squats', sets=3, repetitions=10, order=1)
        cls.diet = DietPlan.objects.create(
            title='Test Diet', goal='Fat loss', calories=1800, created_by_expert=cls.expert,
        )
        DietPlanMeal.objects.create(diet_plan=cls.diet, meal_type='Breakfast', meal_name='Oats', calories=350, order=1)

        cls.plan = MembershipPlan.objects.create(name='Monthly', amount=29, duration_in_months=1)
        cls.event = Event.objects.create(
            title='Test Event', venue='Hall A', event_date=today + timedelta(days=10),
            start_time='09:00', end_time='11:00', capacity=5, status='Open', created_by=cls.admin,
        )


# ---------------------------------------------------------------------------
# Registration & authentication
# ---------------------------------------------------------------------------
class RegistrationTests(TestCase):
    def test_registration_creates_user_with_role_and_profile(self):
        response = self.client.post(reverse('register'), {
            'username': 'newbie', 'email': 'newbie@example.com',
            'first_name': 'New', 'last_name': 'Bee',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='newbie')
        self.assertTrue(user.groups.filter(name=ROLE_USER).exists())
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(user.check_password(PASSWORD))

    def test_registration_duplicate_email_rejected(self):
        make_user('existing', ROLE_USER, email='dup@example.com')
        response = self.client.post(reverse('register'), {
            'username': 'newbie2', 'email': 'dup@example.com',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_registration_password_mismatch_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'newbie3', 'email': 'newbie3@example.com',
            'password1': PASSWORD, 'password2': 'Different123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newbie3').exists())


class LoginLogoutTests(BaseSetup):
    def test_valid_login_redirects_by_role(self):
        cases = [
            (self.admin, 'admin_dashboard'),
            (self.trainer_user, 'trainer_dashboard'),
            (self.expert_user, 'expert_dashboard'),
            (self.user, 'user_dashboard'),
        ]
        for user, expected in cases:
            client = Client()
            response = client.post(reverse('login'), {'username': user.username, 'password': PASSWORD})
            self.assertRedirects(response, reverse(expected), msg_prefix=user.username)

    def test_invalid_login_rejected(self):
        response = self.client.post(reverse('login'), {'username': 'user', 'password': 'wrong-password'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_logout_redirects_to_landing(self):
        self.client.login(username='user', password=PASSWORD)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('landing'))

    def test_anonymous_logout_redirects_without_error(self):
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('landing'))

    def test_dashboard_redirect_by_role(self):
        for user, expected in [
            (self.admin, 'admin_dashboard'), (self.trainer_user, 'trainer_dashboard'),
            (self.expert_user, 'expert_dashboard'), (self.user, 'user_dashboard'),
        ]:
            client = Client()
            client.force_login(user)
            response = client.get(reverse('dashboard_redirect'))
            self.assertRedirects(response, reverse(expected))

    def test_password_change(self):
        self.client.login(username='user', password=PASSWORD)
        response = self.client.post(reverse('change_password'), {
            'old_password': PASSWORD, 'new_password': 'NewPass123!', 'confirm_password': 'NewPass123!',
        })
        self.assertRedirects(response, reverse('user_dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_password_change_wrong_old_password(self):
        self.client.login(username='user', password=PASSWORD)
        response = self.client.post(reverse('change_password'), {
            'old_password': 'nope', 'new_password': 'NewPass123!', 'confirm_password': 'NewPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
class PermissionTests(BaseSetup):
    def _assert_forbidden(self, url, allowed, forbidden):
        for user in allowed:
            client = Client()
            client.force_login(user)
            self.assertEqual(client.get(url).status_code, 200, f'{user.username} should access {url}')
        for user in forbidden:
            client = Client()
            client.force_login(user)
            self.assertEqual(client.get(url).status_code, 302, f'{user.username} must NOT access {url}')

    def test_admin_pages_admin_only(self):
        self._assert_forbidden(reverse('manage_users'), [self.admin], [self.trainer_user, self.expert_user, self.user])
        self._assert_forbidden(reverse('payment_reports'), [self.admin], [self.trainer_user, self.expert_user, self.user])

    def test_trainer_pages_trainer_only(self):
        self._assert_forbidden(reverse('trainer_dashboard'), [self.trainer_user], [self.expert_user, self.user])

    def test_expert_pages_expert_only(self):
        self._assert_forbidden(reverse('expert_dashboard'), [self.expert_user], [self.trainer_user, self.user])

    def test_trainer_cannot_view_unassigned_member(self):
        client = Client()
        client.force_login(self.trainer_user)
        # other_user is not in any of the trainer's batches
        response = client.get(reverse('member_health', args=[self.other_user.id]))
        self.assertEqual(response.status_code, 302)

    def test_user_cannot_view_another_users_data(self):
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('member_health', args=[self.other_user.id]))
        self.assertEqual(response.status_code, 302)

    def test_expert_cannot_edit_another_experts_content(self):
        other_expert = ExpertProfile.objects.create(user=self.other_user, full_name='Other Expert', email='other@example.com')
        other_diet = DietPlan.objects.create(title='Other Diet', created_by_expert=other_expert)
        client = Client()
        client.force_login(self.expert_user)
        response = client.get(reverse('expert_diet_edit', args=[other_diet.id]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# Profile & health
# ---------------------------------------------------------------------------
class ProfileTests(BaseSetup):
    def test_user_profile_update(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('user_profile'), {
            'full_name': 'Updated Name', 'email': 'user@example.com', 'mobile_number': '+1 555 123 4567',
            'gender': 'Male', 'fitness_goal': 'Build muscle', 'activity_level': 'Advanced',
        })
        self.assertRedirects(response, reverse('user_profile'))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, 'Updated Name')

    def test_profile_image_validation(self):
        client = Client()
        client.force_login(self.user)
        bad_file = SimpleUploadedFile('evil.exe', b'not an image', content_type='application/octet-stream')
        response = client.post(reverse('user_profile'), {'full_name': 'X', 'email': 'user@example.com', 'profile_image': bad_file})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'file extension')

    def test_health_details_update_creates_record(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('user_health'), {
            'gender': 'Female', 'fitness_goal': 'Lose weight', 'activity_level': 'Intermediate',
            'height': '170', 'weight': '70',
        })
        self.assertRedirects(response, reverse('user_health'))
        record = HealthRecord.objects.filter(user=self.user).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.height, 170)
        self.assertAlmostEqual(record.bmi, round(70 / (1.7 ** 2), 1))


# ---------------------------------------------------------------------------
# Trainer workflows
# ---------------------------------------------------------------------------
class TrainerWorkflowTests(BaseSetup):
    def test_admin_assigns_trainer_to_batch(self):
        client = Client()
        client.force_login(self.admin)
        response = client.post(reverse('trainer_assign_batch', args=[self.trainer.id]), {'batch': self.batch2.id})
        self.assertRedirects(response, reverse('trainer_assign_batch', args=[self.trainer.id]))
        self.assertTrue(TrainerAssignment.objects.filter(batch=self.batch2, trainer=self.trainer).exists())

    def test_admin_allocates_user_to_batch(self):
        client = Client()
        client.force_login(self.admin)
        response = client.post(reverse('user_batch', args=[self.other_user.id]), {'batch': self.batch2.id, 'status': 'Active'})
        self.assertRedirects(response, reverse('user_batch', args=[self.other_user.id]))
        self.assertTrue(BatchMembership.objects.filter(batch=self.batch2, user=self.other_user).exists())

    def test_workout_plan_creation_and_assignment(self):
        client = Client()
        client.force_login(self.trainer_user)
        response = client.post(reverse('trainer_workout_create'), {
            'title': 'New Plan', 'goal': 'Endurance', 'difficulty_level': 'Intermediate',
            'duration_weeks': 4, 'is_active': 'on',
            'exercises-TOTAL_FORMS': '2', 'exercises-INITIAL_FORMS': '0', 'exercises-MIN_NUM_FORMS': '0', 'exercises-MAX_NUM_FORMS': '1000',
            'exercises-0-exercise_name': 'Running', 'exercises-0-sets': '1', 'exercises-0-repetitions': '1',
            'exercises-0-duration': '20 minutes', 'exercises-0-order': '1',
        })
        self.assertRedirects(response, reverse('trainer_workout_plans'))
        plan = WorkoutPlan.objects.get(title='New Plan')
        self.assertEqual(plan.exercises.count(), 1)

        response = client.post(reverse('trainer_workout_assign', args=[plan.id]), {
            'target_type': 'user', 'user': self.user.id,
        })
        self.assertRedirects(response, reverse('trainer_workout_plans'))
        self.assertTrue(UserWorkoutAssignment.objects.filter(workout_plan=plan, user=self.user).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user, title__icontains='Workout').exists())

    def test_attendance_marking(self):
        client = Client()
        client.force_login(self.trainer_user)
        response = client.post(reverse('trainer_attendance_mark'), {
            'batch': self.batch.id, 'date': date.today().isoformat(), 'present': [str(self.user.id)],
        })
        self.assertRedirects(response, reverse('trainer_attendance'))
        record = Attendance.objects.get(user=self.user, batch=self.batch)
        self.assertEqual(record.status, 'Present')

    def test_trainer_adds_health_record(self):
        client = Client()
        client.force_login(self.trainer_user)
        response = client.post(reverse('member_health_add', args=[self.user.id]), {
            'height': '175', 'weight': '80', 'bmi': '', 'blood_pressure': '120/80',
        })
        self.assertRedirects(response, reverse('member_health', args=[self.user.id]))
        self.assertTrue(HealthRecord.objects.filter(user=self.user, weight=80).exists())

    def test_trainer_adds_progress_record(self):
        client = Client()
        client.force_login(self.trainer_user)
        response = client.post(reverse('member_progress_add', args=[self.user.id]), {
            'weight': '79.5', 'waist_measurement': '90', 'body_fat_percentage': '22', 'progress_note': 'Good progress',
        })
        self.assertRedirects(response, reverse('member_health', args=[self.user.id]))
        self.assertTrue(ProgressRecord.objects.filter(user=self.user, weight=79.5).exists())


# ---------------------------------------------------------------------------
# Expert workflows
# ---------------------------------------------------------------------------
class ExpertWorkflowTests(BaseSetup):
    def test_expert_creates_diet_plan(self):
        client = Client()
        client.force_login(self.expert_user)
        response = client.post(reverse('expert_diet_create'), {
            'title': 'Vegan Lean', 'goal': 'Fat loss', 'calories': '1700', 'dietary_preference': 'Vegan', 'is_active': 'on',
            'meals-TOTAL_FORMS': '1', 'meals-INITIAL_FORMS': '0', 'meals-MIN_NUM_FORMS': '0', 'meals-MAX_NUM_FORMS': '1000',
            'meals-0-meal_type': 'Breakfast', 'meals-0-meal_name': 'Smoothie', 'meals-0-calories': '300', 'meals-0-order': '1',
        })
        self.assertRedirects(response, reverse('expert_diet_plans'))
        plan = DietPlan.objects.get(title='Vegan Lean')
        self.assertEqual(plan.meals.count(), 1)

    def test_expert_assigns_diet_plan(self):
        client = Client()
        client.force_login(self.expert_user)
        response = client.post(reverse('expert_diet_assign', args=[self.diet.id]), {'users': [str(self.user.id)]})
        self.assertRedirects(response, reverse('expert_diet_plans'))
        self.assertTrue(UserDietAssignment.objects.filter(diet_plan=self.diet, user=self.user).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user, title__icontains='Diet').exists())

    def test_expert_creates_video_and_tip(self):
        client = Client()
        client.force_login(self.expert_user)
        response = client.post(reverse('expert_video_create'), {
            'title': 'Demo Video', 'description': 'How-to', 'category': 'Strength', 'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'is_active': 'on',
        })
        self.assertRedirects(response, reverse('expert_videos'))
        self.assertTrue(FitnessVideo.objects.filter(title='Demo Video').exists())

        response = client.post(reverse('expert_tip_create'), {
            'title': 'Hydration tip', 'content': 'Drink water.', 'category': 'Nutrition', 'is_published': 'on',
        })
        self.assertRedirects(response, reverse('expert_tips'))
        self.assertTrue(WellnessTip.objects.filter(title='Hydration tip', author=self.expert_user).exists())

    def test_video_requires_url_or_file(self):
        client = Client()
        client.force_login(self.expert_user)
        response = client.post(reverse('expert_video_create'), {
            'title': 'No Source', 'description': 'x', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Provide either a video URL')

    def test_video_file_upload_validation(self):
        client = Client()
        client.force_login(self.expert_user)
        bad = SimpleUploadedFile('clip.txt', b'hello', content_type='text/plain')
        response = client.post(reverse('expert_video_create'), {
            'title': 'Bad Upload', 'description': 'x', 'uploaded_file': bad, 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'file extension')


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
class EventTests(BaseSetup):
    def test_event_registration(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('register_event', args=[self.event.id]))
        self.assertRedirects(response, reverse('event_list'))
        self.assertTrue(EventRegistration.objects.filter(event=self.event, user=self.user).exists())

    def test_duplicate_event_registration_prevented(self):
        EventRegistration.objects.create(event=self.event, user=self.user)
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('register_event', args=[self.event.id]))
        self.assertRedirects(response, reverse('event_list'))
        self.assertEqual(EventRegistration.objects.filter(event=self.event, user=self.user).count(), 1)

    def test_event_full_rejected(self):
        EventRegistration.objects.create(event=self.event, user=self.other_user)
        # capacity is 5, so add 4 more to fill it
        for i in range(4):
            u = make_user(f'filler{i}', ROLE_USER)
            EventRegistration.objects.create(event=self.event, user=u)
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('register_event', args=[self.event.id]))
        self.assertRedirects(response, reverse('event_list'))
        self.assertFalse(EventRegistration.objects.filter(event=self.event, user=self.user).exists())

    def test_admin_creates_event(self):
        client = Client()
        client.force_login(self.admin)
        response = client.post(reverse('event_create'), {
            'title': 'Admin Event', 'venue': 'Main Hall', 'event_date': date.today() + timedelta(days=15),
            'start_time': '10:00', 'end_time': '12:00', 'capacity': 20, 'status': 'Open',
        })
        self.assertRedirects(response, reverse('manage_events'))
        self.assertTrue(Event.objects.filter(title='Admin Event').exists())


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
class PaymentTests(BaseSetup):
    def test_payment_creation(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('pay_now', args=[self.plan.id]))
        self.assertRedirects(response, reverse('user_payments'))
        payment = Payment.objects.get(user=self.user, membership_plan=self.plan)
        self.assertEqual(payment.status, 'Paid')
        self.assertEqual(payment.payment_month, date.today().strftime('%B'))

    def test_due_payment_alerts(self):
        # user has no payment this month -> due
        client = Client()
        client.force_login(self.admin)
        response = client.post(reverse('due_remind'))
        self.assertRedirects(response, reverse('due_payments'))
        self.assertTrue(PaymentAlert.objects.filter(user=self.user).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user, title__icontains='reminder').exists())

    def test_admin_payment_report_filter(self):
        Payment.objects.create(
            user=self.user, membership_plan=self.plan, amount=29,
            payment_month='January', payment_year='2025', status='Paid',
        )
        client = Client()
        client.force_login(self.admin)
        response = client.get(reverse('payment_reports'), {'month': 'January', 'year': '2025'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_collected'], 29)


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
class ChatTests(BaseSetup):
    def test_user_starts_chat_with_trainer_and_sends_message(self):
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('chat_start', args=['trainer', self.trainer.id]))
        conversation = ChatConversation.objects.get(user=self.user, trainer=self.trainer_user)
        self.assertRedirects(response, reverse('chat_thread', args=[conversation.id]))
        response = client.post(reverse('chat_thread', args=[conversation.id]), {'message': 'Hello coach!'})
        self.assertRedirects(response, reverse('chat_thread', args=[conversation.id]))
        message = ChatMessage.objects.get(conversation=conversation, sender=self.user)
        self.assertEqual(message.message, 'Hello coach!')

    def test_user_cannot_access_foreign_conversation(self):
        conversation = ChatConversation.objects.create(user=self.other_user, trainer=self.trainer_user)
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('chat_thread', args=[conversation.id]))
        self.assertRedirects(response, reverse('chat_home'))


# ---------------------------------------------------------------------------
# Feedback & notifications
# ---------------------------------------------------------------------------
class FeedbackTests(BaseSetup):
    def test_feedback_submission_and_response(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('feedback_form'), {'subject': 'Great app', 'message': 'Love it', 'rating': '5'})
        self.assertRedirects(response, reverse('feedback_my'))
        feedback = Feedback.objects.get(user=self.user)
        self.assertEqual(feedback.status, 'Open')

        admin_client = Client()
        admin_client.force_login(self.admin)
        response = admin_client.post(reverse('feedback_respond', args=[feedback.id]), {
            'response': 'Thanks!', 'status': 'Resolved',
        })
        self.assertRedirects(response, reverse('feedback_list'))
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, 'Resolved')
        self.assertTrue(Notification.objects.filter(recipient=self.user, title__icontains='Feedback').exists())

    def test_notifications_mark_read(self):
        notification = Notification.objects.create(recipient=self.user, title='Test', message='Hi')
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('notification_mark_read', args=[notification.id]))
        self.assertRedirects(response, reverse('notifications_list'))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)


# ---------------------------------------------------------------------------
# Form & model validation
# ---------------------------------------------------------------------------
class ValidationTests(BaseSetup):
    def test_batch_end_before_start_rejected(self):
        from admin_panel.forms import BatchForm
        form = BatchForm(data={
            'name': 'Bad', 'start_date': date.today() + timedelta(days=10),
            'end_date': date.today(), 'capacity': 10, 'status': 'Active',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_batch_unique_membership(self):
        with self.assertRaises(Exception):
            BatchMembership.objects.create(batch=self.batch, user=self.user)

    def test_trainer_unique_assignment(self):
        with self.assertRaises(Exception):
            TrainerAssignment.objects.create(batch=self.batch, trainer=self.trainer)

    def test_event_unique_registration(self):
        EventRegistration.objects.create(event=self.event, user=self.user)
        with self.assertRaises(Exception):
            EventRegistration.objects.create(event=self.event, user=self.user)

    def test_duplicate_registration_email_rejected(self):
        from accounts.forms import CustomUserRegistrationForm
        make_user('taken', ROLE_USER, email='taken@example.com')
        form = CustomUserRegistrationForm(data={
            'username': 'someone', 'email': 'taken@example.com',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertFalse(form.is_valid())


# ---------------------------------------------------------------------------
# Dashboards & API
# ---------------------------------------------------------------------------
class DashboardTests(BaseSetup):
    def test_all_dashboards_load(self):
        for user, url in [
            (self.admin, reverse('admin_dashboard')),
            (self.trainer_user, reverse('trainer_dashboard')),
            (self.expert_user, reverse('expert_dashboard')),
            (self.user, reverse('user_dashboard')),
        ]:
            client = Client()
            client.force_login(user)
            self.assertEqual(client.get(url).status_code, 200, user.username)

    def test_api_endpoints_require_auth(self):
        response = self.client.get('/api/summary/')
        self.assertEqual(response.status_code, 403)
        client = Client()
        client.force_login(self.user)
        response = client.get('/api/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('role', response.json())

    def test_api_notifications(self):
        Notification.objects.create(recipient=self.user, title='API test', message='x')
        client = Client()
        client.force_login(self.user)
        response = client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_public_pages_load(self):
        for url in ['/', '/about/', '/features/', '/trainers/', '/experts/', '/resources/', '/contact/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)