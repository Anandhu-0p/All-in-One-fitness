"""Seed demo data for All-in-One Fitness.

Usage:
    python manage.py seed_demo_data          # idempotent - creates only what is missing
    python manage.py seed_demo_data --reset  # deletes demo-created data first, then re-seeds
"""
from datetime import date, datetime, timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.models import PlatformContent, UserProfile
from accounts.utils import ROLE_EXPERT, ROLE_TRAINER, ROLE_USER, assign_role
from chat.models import ChatConversation, ChatMessage
from events.models import Event, EventRegistration
from experts.models import DietPlan, DietPlanMeal, ExpertProfile, FitnessVideo, UserDietAssignment, WellnessTip
from fitness.models import UserWorkoutAssignment, WorkoutExercise, WorkoutPlan
from notifications.models import ActivityLog, Feedback, Notification
from payments.models import MembershipPlan, Payment, PaymentAlert
from trainers.models import Attendance, Batch, BatchMembership, TrainerAssignment, TrainerProfile
from users.models import HealthRecord, ProgressRecord

DEMO_PASSWORD = 'Fitness@123'


def _ensure_user(username, email, first, last, role, password=DEMO_PASSWORD):
    """Create or update a demo account, always ensuring the demo password works."""
    user = User.objects.filter(username=username).first()
    created = False
    if user is None:
        user = User.objects.create_user(username=username, email=email, first_name=first, last_name=last)
        created = True
    user.email = email
    user.first_name = first
    user.last_name = last
    user.is_active = True
    user.set_password(password)  # demo accounts always use the documented demo password
    user.save()
    assign_role(user, role)
    return user, created


class Command(BaseCommand):
    help = 'Create demo accounts and sample data for all four roles.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete previously seeded demo data first.')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()
            self.stdout.write(self.style.WARNING('Demo data reset.'))

        for name in (ROLE_TRAINER, ROLE_EXPERT, ROLE_USER):
            Group.objects.get_or_create(name=name)

        # ---- Accounts ----------------------------------------------------
        admin, _ = _ensure_user('admin', 'admin@example.com', 'Arun', 'Nair', ROLE_ADMIN := 'Admin')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        trainer_user, _ = _ensure_user('trainer', 'trainer@example.com', 'Vishnu', 'Menon', ROLE_TRAINER)
        expert_user, _ = _ensure_user('expert', 'expert@example.com', 'Anjali', 'Pillai', ROLE_EXPERT)
        user_user, _ = _ensure_user('user', 'user@example.com', 'Akhil', 'Krishnan', ROLE_USER)

        trainer2_user, _ = _ensure_user('trainer2', 'priya@example.com', 'Deepa', 'Varma', ROLE_TRAINER)
        expert2_user, _ = _ensure_user('expert2', 'sara@example.com', 'Sreelakshmi', 'Menon', ROLE_EXPERT)
        user2, _ = _ensure_user('member2', 'member2@example.com', 'Nikhil', 'Madhavan', ROLE_USER)
        user3, _ = _ensure_user('member3', 'member3@example.com', 'Lakshmi', 'Suresh', ROLE_USER)

        trainer, _ = TrainerProfile.objects.update_or_create(user=trainer_user, defaults={
            'full_name': 'Vishnu Menon', 'email': 'trainer@example.com', 'mobile_number': '+91 98765 61001',
            'specialization': 'Strength & Conditioning', 'qualification': 'ACE Certified PT India',
            'experience': 8, 'bio': 'Certified strength coach helping members build sustainable training habits.',
        })
        TrainerProfile.objects.update_or_create(user=trainer2_user, defaults={
            'full_name': 'Deepa Varma', 'email': 'priya@example.com', 'mobile_number': '+91 98765 61002',
            'specialization': 'HIIT & Functional Training', 'qualification': 'NASM CPT India',
            'experience': 6, 'bio': 'High-energy HIIT coach who makes every session count.',
        })
        expert, _ = ExpertProfile.objects.update_or_create(user=expert_user, defaults={
            'full_name': 'Dr Anjali Pillai', 'email': 'expert@example.com', 'mobile_number': '+91 98765 62001',
            'specialization': 'Sports Nutrition', 'qualification': 'MSc Nutrition & Dietetics',
            'bio': 'Nutrition scientist creating practical, allergy-aware meal plans.',
        })
        ExpertProfile.objects.update_or_create(user=expert2_user, defaults={
            'full_name': 'Sreelakshmi Menon', 'email': 'sara@example.com', 'mobile_number': '+91 98765 62002',
            'specialization': 'Weight Management', 'qualification': 'RD, CDE',
            'bio': 'Registered dietitian focused on sustainable weight management.',
        })

        for u, name, email, phone, address, goal in [
            (user_user, 'Akhil Krishnan', 'user@example.com', '+91 98765 63001', 'Vyttila, Ernakulam, Kerala', 'Lose weight'),
            (user2, 'Nikhil Madhavan', 'member2@example.com', '+91 98765 63002', 'Kowdiar, Thiruvananthapuram, Kerala', 'Improve endurance'),
            (user3, 'Lakshmi Suresh', 'member3@example.com', '+91 98765 63003', 'Nadakkavu, Kozhikode, Kerala', 'Flexibility & strength'),
        ]:
            profile, _ = UserProfile.objects.update_or_create(user=u, defaults={
                'full_name': name, 'email': email, 'mobile_number': phone, 'address': address,
                'gender': 'Other', 'fitness_goal': goal, 'activity_level': 'Intermediate',
                'dietary_preference': 'Vegetarian' if u != user2 else 'High-protein',
            })

        self.stdout.write(self.style.SUCCESS('Accounts ready.'))

        # ---- Batches -----------------------------------------------------
        today = date.today()
        batch_a, _ = Batch.objects.update_or_create(name='Morning Warriors', defaults={
            'description': 'Early-bird strength and conditioning batch.',
            'start_date': today, 'end_date': today + timedelta(days=180),
            'schedule': 'Mon/Wed/Fri 6:00 AM IST', 'capacity': 20, 'status': 'Active',
        })
        batch_b, _ = Batch.objects.update_or_create(name='Evening Fit', defaults={
            'description': 'Evening HIIT and functional training.',
            'start_date': today, 'end_date': today + timedelta(days=150),
            'schedule': 'Tue/Thu 7:00 PM IST', 'capacity': 25, 'status': 'Active',
        })
        batch_c, _ = Batch.objects.update_or_create(name='Weekend Bootcamp', defaults={
            'description': 'Saturday group bootcamps and endurance work.',
            'start_date': today + timedelta(days=7), 'end_date': today + timedelta(days=200),
            'schedule': 'Sat 8:00 AM IST', 'capacity': 30, 'status': 'Upcoming',
        })
        Batch.objects.update_or_create(name='Sunrise Stretch', defaults={
            'description': 'Morning mobility and yoga-focused batch.',
            'start_date': today, 'end_date': today + timedelta(days=120),
            'schedule': 'Sun 7:00 AM IST', 'capacity': 15, 'status': 'Active',
        })

        for batch, member in [(batch_a, user_user), (batch_a, user2), (batch_b, user3)]:
            BatchMembership.objects.get_or_create(batch=batch, user=member, defaults={'status': 'Active'})
        for batch, tr in [(batch_a, trainer), (batch_b, trainer), (batch_a, TrainerProfile.objects.get(user=trainer2_user)), (batch_c, trainer)]:
            TrainerAssignment.objects.get_or_create(batch=batch, trainer=tr, defaults={'status': 'Active'})

        # ---- Membership plans --------------------------------------------
        monthly, _ = MembershipPlan.objects.get_or_create(name='Monthly', defaults={
            'description': 'Full access for one month.', 'amount': 2900, 'duration_in_months': 1,
        })
        quarterly, _ = MembershipPlan.objects.get_or_create(name='Quarterly', defaults={
            'description': 'Three months of full access — save 10%.', 'amount': 7800, 'duration_in_months': 3,
        })
        yearly, _ = MembershipPlan.objects.get_or_create(name='Yearly', defaults={
            'description': 'Best value: twelve months of full access.', 'amount': 29000, 'duration_in_months': 12,
        })

        # ---- Workout plans -----------------------------------------------
        plan1, _ = WorkoutPlan.objects.get_or_create(title='Lean Body Builder', defaults={
            'description': 'A 6-week progressive plan combining strength and cardio for fat loss.',
            'goal': 'Fat loss', 'difficulty_level': 'Intermediate', 'duration_weeks': 6,
            'created_by_trainer': trainer, 'is_active': True,
        })
        plan2, _ = WorkoutPlan.objects.get_or_create(title='Beginner Foundations', defaults={
            'description': 'Learn the fundamentals: form, consistency and habit building.',
            'goal': 'General fitness', 'difficulty_level': 'Beginner', 'duration_weeks': 4,
            'created_by_trainer': trainer, 'is_active': True,
        })
        WorkoutPlan.objects.get_or_create(title='HIIT Conditioning', defaults={
            'description': 'High-intensity intervals to boost endurance and burn calories.',
            'goal': 'Endurance', 'difficulty_level': 'Advanced', 'duration_weeks': 5,
            'created_by_trainer': TrainerProfile.objects.get(user=trainer2_user), 'is_active': True,
        })

        for plan, exercises in [
            (plan1, [
                ('Push-ups', 'Chest and triceps compound', 3, 15, '45 seconds', '60 seconds'),
                ('Squats', 'Lower body strength', 3, 20, '60 seconds', '60 seconds'),
                ('Plank', 'Core stability', 3, 1, '45 seconds', '45 seconds'),
                ('Mountain climbers', 'Cardio and core', 3, 20, '45 seconds', '30 seconds'),
            ]),
            (plan2, [
                ('Bodyweight squat', 'Learn the squat pattern', 2, 12, '30 seconds', '60 seconds'),
                ('Incline push-up', 'Easier push-up variation', 2, 10, '30 seconds', '60 seconds'),
                ('Dead bug', 'Core activation', 2, 10, '30 seconds', '45 seconds'),
            ]),
        ]:
            if not plan.exercises.exists():
                for i, (name, desc, sets, reps, duration, rest) in enumerate(exercises, start=1):
                    WorkoutExercise.objects.create(
                        workout_plan=plan, exercise_name=name, description=desc, sets=sets,
                        repetitions=reps, duration=duration, rest_time=rest, order=i,
                    )

        for plan, member in [(plan1, user_user), (plan2, user2)]:
            UserWorkoutAssignment.objects.get_or_create(
                workout_plan=plan, user=member,
                defaults={'assigned_by': trainer_user, 'start_date': today, 'status': 'Active'},
            )

        # ---- Diet plans --------------------------------------------------
        diet1, _ = DietPlan.objects.get_or_create(title='Lean & Green', defaults={
            'description': 'Balanced vegetarian plan for steady fat loss.',
            'goal': 'Fat loss', 'calories': 1800, 'dietary_preference': 'Vegetarian',
            'created_by_expert': expert, 'is_active': True,
        })
        diet2, _ = DietPlan.objects.get_or_create(title='Muscle Fuel', defaults={
            'description': 'High-protein plan to support muscle gain and recovery.',
            'goal': 'Muscle gain', 'calories': 2600, 'dietary_preference': 'High-protein',
            'created_by_expert': expert, 'is_active': True,
        })
        DietPlan.objects.get_or_create(title='Endurance Energy', defaults={
            'description': 'Carb-aware plan for runners and endurance athletes.',
            'goal': 'Endurance', 'calories': 2400, 'dietary_preference': 'Balanced',
            'created_by_expert': ExpertProfile.objects.get(user=expert2_user), 'is_active': True,
        })

        for plan, meals in [
            (diet1, [
                ('Breakfast', 'Oats with berries', 'Rolled oats, almond milk, mixed berries.', 350, 1),
                ('Lunch', 'Quinoa bowl', 'Quinoa, chickpeas, roasted vegetables, tahini dressing.', 520, 2),
                ('Snack', 'Greek yoghurt & nuts', 'Greek yoghurt with a small handful of almonds.', 200, 3),
                ('Dinner', 'Grilled paneer salad', 'Grilled paneer, leafy greens, cucumber, olive oil.', 480, 4),
            ]),
            (diet2, [
                ('Breakfast', 'Egg white omelette', 'Egg whites, spinach, whole wheat toast.', 420, 1),
                ('Lunch', 'Chicken rice bowl', 'Grilled chicken breast, brown rice, broccoli.', 640, 2),
                ('Post-workout', 'Protein shake', 'Whey protein with banana and oats.', 300, 3),
                ('Dinner', 'Salmon & sweet potato', 'Baked salmon, sweet potato mash, green beans.', 590, 4),
            ]),
        ]:
            if not plan.meals.exists():
                for meal_type, name, desc, calories, order in meals:
                    DietPlanMeal.objects.create(
                        diet_plan=plan, meal_type=meal_type, meal_name=name,
                        description=desc, calories=calories, order=order,
                    )

        UserDietAssignment.objects.get_or_create(
            diet_plan=diet1, user=user_user, defaults={'assigned_by': expert_user, 'start_date': today, 'status': 'Active'},
        )
        UserDietAssignment.objects.get_or_create(
            diet_plan=diet2, user=user2, defaults={'assigned_by': expert_user, 'start_date': today, 'status': 'Active'},
        )

        # ---- Videos & tips -----------------------------------------------
        for title, category, desc in [
            ('Perfect Squat Form', 'Strength', 'Learn the squat pattern step by step.'),
            ('10-Minute Morning Mobility', 'Mobility', 'Quick routine to start your day.'),
            ('Beginner Yoga Flow', 'Yoga', 'Gentle flow for flexibility and calm.'),
        ]:
            FitnessVideo.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc, 'category': category,
                    'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'uploaded_by_expert': expert, 'is_active': True,
                },
            )

        for title, content, category in [
            ('Hydrate before you feel thirsty', 'Drink water consistently through the day — thirst is a late signal.', 'Nutrition'),
            ('Sleep is part of training', 'Aim for 7–9 hours; recovery happens while you sleep.', 'Sleep'),
            ('Protein at every meal', 'Spread protein across meals to support muscle repair and satiety.', 'Nutrition'),
            ('Breathe through the hard sets', 'Exhale on effort to keep your core braced and your mind calm.', 'Mental health'),
        ]:
            WellnessTip.objects.get_or_create(
                title=title,
                defaults={'content': content, 'category': category, 'author': expert_user, 'is_published': True},
            )

        # ---- Events ------------------------------------------------------
        for title, days_ahead, venue, capacity in [
            ('Bootcamp Saturday', 5, 'Marine Drive, Kochi, Kerala', 30),
            ('Nutrition Masterclass', 12, 'Kakkanad Fitness Studio, Kochi, Kerala', 40),
            ('Mind & Movement Workshop', 20, 'Kovalam Wellness Centre, Thiruvananthapuram', 25),
            ('Summer Fitness Challenge Launch', 30, 'Lulu Convention Centre, Thrissur, Kerala', 50),
        ]:
            event, _ = Event.objects.update_or_create(title=title, defaults={
                'description': f'Join our {title.lower()} event — open to all members.',
                'venue': venue, 'event_date': today + timedelta(days=days_ahead),
                'start_time': datetime.strptime('09:00', '%H:%M').time(),
                'end_time': datetime.strptime('11:00', '%H:%M').time(),
                'capacity': capacity, 'created_by': admin, 'status': 'Open',
            })
            EventRegistration.objects.get_or_create(event=event, user=user_user, defaults={'status': 'Registered'})

        # ---- Payments -----------------------------------------------------
        Payment.objects.get_or_create(
            transaction_id='DEMO-PAID-001',
                defaults={
                    'user': user_user, 'membership_plan': monthly,
                    'amount': monthly.amount, 'payment_month': today.strftime('%B'), 'payment_year': str(today.year),
                'payment_method': 'Demo Card (•••• 4242)', 'transaction_id': 'DEMO-PAID-001', 'status': 'Paid',
            },
        )
        Payment.objects.get_or_create(
            transaction_id='DEMO-PEND-002',
                defaults={
                    'user': user2, 'membership_plan': quarterly,
                    'amount': quarterly.amount, 'payment_month': today.strftime('%B'), 'payment_year': str(today.year),
                'payment_method': 'Bank transfer', 'transaction_id': 'DEMO-PEND-002', 'status': 'Pending',
            },
        )
        if not Payment.objects.filter(user=user3).exists():
            Payment.objects.create(
                user=user3, membership_plan=monthly, amount=monthly.amount,
                payment_month=(today - timedelta(days=35)).strftime('%B'),
                payment_year=str((today - timedelta(days=35)).year),
                payment_method='Cash', transaction_id='DEMO-OLD-003', status='Overdue',
            )
        PaymentAlert.objects.get_or_create(
            user=user3,
            defaults={
                'message': f'Your membership payment for {today.strftime("%B %Y")} is overdue. Please pay to keep your membership active.',
                'due_date': today, 'is_read': False,
            },
        )

        # ---- Attendance, health & progress -------------------------------
        if not Attendance.objects.filter(user=user_user).exists():
            for i in range(1, 26):
                d = today - timedelta(days=31 - i)
                if d.weekday() in (0, 2, 4):  # Mon/Wed/Fri
                    Attendance.objects.get_or_create(
                        user=user_user, batch=batch_a, date=d,
                        defaults={'trainer': trainer, 'status': 'Present' if i % 7 != 3 else 'Absent'},
                    )
        if not HealthRecord.objects.filter(user=user_user).exists():
            for i, weight in enumerate([84, 83.2, 82.1, 81.4, 80.2, 79.5]):
                HealthRecord.objects.create(
                    user=user_user, height=178, weight=weight,
                    bmi=round(weight / (1.78 ** 2), 1), body_fat_percentage=round(24 - i * 0.4, 1),
                    blood_pressure='120/80', recorded_by=trainer_user,
                )
        if not ProgressRecord.objects.filter(user=user_user).exists():
            for i, weight in enumerate([84.5, 83.8, 82.9, 82.0, 81.2, 80.4]):
                ProgressRecord.objects.create(
                    user=user_user, weight=weight, waist_measurement=round(92 - i * 0.8, 1),
                    body_fat_percentage=round(25 - i * 0.5, 1),
                    progress_note=f'Week {i + 1} check-in',
                )

        # ---- Notifications, feedback, chat, logs -------------------------
        Notification.objects.get_or_create(
            recipient=user_user, title='Workout plan assigned',
            defaults={'message': 'Your trainer assigned you the plan "Lean Body Builder".', 'notification_type': 'info'},
        )
        Notification.objects.get_or_create(
            recipient=user_user, title='Diet plan assigned',
            defaults={'message': 'Your expert assigned you the diet plan "Lean & Green".', 'notification_type': 'info'},
        )
        Notification.objects.get_or_create(
            recipient=user3, title='Payment reminder',
            defaults={'message': 'Your membership payment is overdue. Please pay to keep your membership active.', 'notification_type': 'warning'},
        )
        Feedback.objects.get_or_create(
            user=user_user, subject='Great training app!',
            defaults={'message': 'The workout plans and attendance tracking keep me consistent.', 'rating': 5, 'status': 'Open'},
        )

        convo, _ = ChatConversation.objects.get_or_create(user=user_user, trainer=trainer_user)
        if not convo.messages.exists():
            ChatMessage.objects.create(conversation=convo, sender=trainer_user, message='Welcome to the Morning Warriors batch! How did your first session feel?')
            ChatMessage.objects.create(conversation=convo, sender=user_user, message='It was great — the plan is challenging but fun!')

        for key, title, content in [
            ('hero_title', 'Hero headline', 'Your Complete Fitness Journey Starts Here'),
            ('hero_subtitle', 'Hero subtitle', 'Train with certified coaches, follow personalised nutrition and workout plans, track your progress, and be part of a community that keeps you moving.'),
            ('benefits_title', 'Benefits title', 'Everything you need, in one place'),
            ('benefits_text', 'Benefits text', 'Personalised workout and diet plans, real trainer guidance, expert nutrition advice, attendance and payment tracking, events, and private messaging.'),
            ('features_title', 'Features title', 'Built for every step of your journey'),
            ('features_text', 'Features text', 'From first-timers to advanced athletes, our platform adapts to your goals.'),
            ('testimonials_title', 'Testimonials title', 'What our members say'),
            ('testimonials_text', 'Testimonials text', 'Real results from real members.'),
            ('faq_title', 'FAQ title', 'Frequently asked questions'),
            ('faq_text', 'FAQ text', 'Quick answers to common questions.'),
        ]:
            PlatformContent.objects.get_or_create(key=key, defaults={'title': title, 'content': content})

        ActivityLog.objects.get_or_create(
            user=admin, action='Demo data seeded', description='Seeded demo accounts and content.',
            defaults={'ip_address': None},
        )

        self.stdout.write(self.style.SUCCESS(
            'Demo data ready.\n'
            '  admin@example.com   (Administrator)  password: Fitness@123\n'
            '  trainer@example.com (Trainer)        password: Fitness@123\n'
            '  expert@example.com  (Expert)         password: Fitness@123\n'
            '  user@example.com    (User)           password: Fitness@123'
        ))

    def _reset(self):
        User.objects.filter(username__in=['admin', 'trainer', 'expert', 'user', 'trainer2', 'expert2', 'member2', 'member3']).delete()
        Batch.objects.all().delete()
        MembershipPlan.objects.all().delete()
        WorkoutPlan.objects.all().delete()
        DietPlan.objects.all().delete()
        FitnessVideo.objects.all().delete()
        WellnessTip.objects.all().delete()
        Event.objects.all().delete()
        Payment.objects.all().delete()
        PaymentAlert.objects.all().delete()
        Attendance.objects.all().delete()
        HealthRecord.objects.all().delete()
        ProgressRecord.objects.all().delete()
        Feedback.objects.all().delete()
        Notification.objects.all().delete()
        ChatConversation.objects.all().delete()
        PlatformContent.objects.all().delete()
        ActivityLog.objects.all().delete()
        TrainerProfile.objects.all().delete()
        ExpertProfile.objects.all().delete()
        UserProfile.objects.all().delete()
        Group.objects.filter(name__in=[ROLE_TRAINER, ROLE_EXPERT, ROLE_USER]).delete()