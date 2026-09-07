from datetime import date

from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.utils import user_role
from chat.models import ChatConversation
from events.models import Event, EventRegistration
from experts.models import FitnessVideo, UserDietAssignment, WellnessTip
from fitness.models import UserWorkoutAssignment
from notifications.models import Notification
from payments.models import Payment
from trainers.models import Attendance
from users.models import ProgressRecord

from .serializers import (
    AttendanceSerializer,
    ChatMessageSerializer,
    DietPlanSerializer,
    EventSerializer,
    FitnessVideoSerializer,
    NotificationSerializer,
    PaymentSerializer,
    ProgressRecordSerializer,
    WellnessTipSerializer,
    WorkoutPlanSerializer,
)


class NotificationsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Notification.objects.filter(recipient=request.user)
        return Response(NotificationSerializer(items, many=True).data)

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'detail': 'All notifications marked as read.'})


class EventsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(status='Open').annotate(registered=Count('registrations'))
        my_ids = EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True)
        data = EventSerializer(events, many=True).data
        for item in data:
            item['registered_by_me'] = item['id'] in my_ids
        return Response(data)


class ProgressAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = ProgressRecord.objects.filter(user=request.user).order_by('-recorded_at')
        return Response(ProgressRecordSerializer(records, many=True).data)

    def post(self, request):
        serializer = ProgressRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Payment.objects.filter(user=request.user).order_by('-payment_date')
        return Response(PaymentSerializer(items, many=True).data)


class WorkoutsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = UserWorkoutAssignment.objects.filter(user=request.user, status='Active').select_related(
            'workout_plan', 'workout_plan__created_by_trainer'
        ).prefetch_related('workout_plan__exercises')
        return Response(WorkoutPlanSerializer(items, many=True).data)


class DietsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = UserDietAssignment.objects.filter(user=request.user, status='Active').select_related(
            'diet_plan', 'diet_plan__created_by_expert'
        )
        return Response(DietPlanSerializer(items, many=True).data)


class AttendanceAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Attendance.objects.filter(user=request.user).order_by('-date')
        return Response(AttendanceSerializer(items, many=True).data)


class ChatMessagesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = ChatConversation.objects.get(id=conversation_id)
        except ChatConversation.DoesNotExist:
            return Response({'detail': 'Conversation not found.'}, status=404)
        allowed = (
            conversation.user == request.user
            or conversation.trainer == request.user
            or conversation.expert == request.user
        )
        if not allowed:
            return Response({'detail': 'Forbidden.'}, status=403)
        messages_qs = conversation.messages.order_by('sent_at')
        return Response(ChatMessageSerializer(messages_qs, many=True).data)


class TipsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WellnessTip.objects.filter(is_published=True).order_by('-created_at')
        return Response(WellnessTipSerializer(items, many=True).data)


class VideosAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = FitnessVideo.objects.filter(is_active=True).order_by('-created_at')
        return Response(FitnessVideoSerializer(items, many=True).data)


class DashboardSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        attendance = Attendance.objects.filter(user=user)
        total_att = attendance.count()
        present_att = attendance.filter(status='Present').count()
        return Response({
            'role': user_role(user),
            'notifications_unread': Notification.objects.filter(recipient=user, is_read=False).count(),
            'active_workouts': UserWorkoutAssignment.objects.filter(user=user, status='Active').count(),
            'active_diets': UserDietAssignment.objects.filter(user=user, status='Active').count(),
            'attendance_percentage': round((present_att / total_att) * 100) if total_att else 0,
            'total_paid': Payment.objects.filter(user=user, status='Paid').count(),
            'upcoming_events': Event.objects.filter(status='Open', event_date__gte=date.today()).count(),
        })