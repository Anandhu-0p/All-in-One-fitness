from rest_framework import serializers

from chat.models import ChatMessage
from events.models import Event
from experts.models import DietPlan, FitnessVideo, UserDietAssignment, WellnessTip
from fitness.models import UserWorkoutAssignment, WorkoutExercise
from notifications.models import Notification
from payments.models import Payment
from trainers.models import Attendance
from users.models import ProgressRecord


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    registered = serializers.IntegerField(read_only=True)
    spots_left = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'venue', 'event_date', 'start_time', 'end_time', 'capacity', 'status', 'registered', 'spots_left']

    def get_spots_left(self, obj):
        return max(0, obj.capacity - obj.registered)


class ProgressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressRecord
        fields = ['id', 'weight', 'waist_measurement', 'body_fat_percentage', 'progress_note', 'recorded_at']


class PaymentSerializer(serializers.ModelSerializer):
    plan = serializers.CharField(source='membership_plan.name', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'plan', 'amount', 'payment_date', 'payment_method', 'transaction_id', 'status']


class AttendanceSerializer(serializers.ModelSerializer):
    batch = serializers.CharField(source='batch.name', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'batch', 'date', 'status', 'notes']


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutExercise
        fields = ['exercise_name', 'description', 'sets', 'repetitions', 'duration', 'rest_time', 'video_url', 'order']


class WorkoutPlanSerializer(serializers.ModelSerializer):
    trainer = serializers.CharField(source='created_by_trainer.full_name', read_only=True)
    exercises = WorkoutExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = UserWorkoutAssignment
        fields = ['id', 'workout_plan', 'trainer', 'start_date', 'end_date', 'status', 'exercises']

    workout_plan = serializers.CharField(source='workout_plan.title', read_only=True)


class DietPlanSerializer(serializers.ModelSerializer):
    expert = serializers.CharField(source='created_by_expert.full_name', read_only=True)

    class Meta:
        model = UserDietAssignment
        fields = ['id', 'diet_plan', 'expert', 'start_date', 'end_date', 'status']

    diet_plan = serializers.CharField(source='diet_plan.title', read_only=True)


class WellnessTipSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = WellnessTip
        fields = ['id', 'title', 'content', 'category', 'created_at']


class FitnessVideoSerializer(serializers.ModelSerializer):
    expert = serializers.CharField(source='uploaded_by_expert.full_name', read_only=True)

    class Meta:
        model = FitnessVideo
        fields = ['id', 'title', 'description', 'category', 'video_url', 'uploaded_file', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'attachment', 'sent_at', 'is_read']