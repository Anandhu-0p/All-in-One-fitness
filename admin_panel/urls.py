from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('profile/', views.admin_profile, name='admin_profile'),

    # Users
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/toggle/', views.user_toggle, name='user_toggle'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/batch/', views.user_batch, name='user_batch'),

    # Trainers
    path('trainers/', views.manage_trainers, name='manage_trainers'),
    path('trainers/add/', views.trainer_add, name='trainer_add'),
    path('trainers/<int:trainer_id>/edit/', views.trainer_edit, name='trainer_edit'),
    path('trainers/<int:trainer_id>/toggle/', views.trainer_toggle, name='trainer_toggle'),
    path('trainers/<int:trainer_id>/delete/', views.trainer_delete, name='trainer_delete'),
    path('trainers/<int:trainer_id>/assign-batch/', views.trainer_assign_batch, name='trainer_assign_batch'),

    # Experts
    path('experts/', views.manage_experts, name='manage_experts'),
    path('experts/add/', views.expert_add, name='expert_add'),
    path('experts/<int:expert_id>/edit/', views.expert_edit, name='expert_edit'),
    path('experts/<int:expert_id>/toggle/', views.expert_toggle, name='expert_toggle'),
    path('experts/<int:expert_id>/delete/', views.expert_delete, name='expert_delete'),

    # Batches
    path('batches/', views.manage_batches, name='manage_batches'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('batches/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:batch_id>/edit/', views.batch_edit, name='batch_edit'),
    path('batches/<int:batch_id>/delete/', views.batch_delete, name='batch_delete'),
    path('batches/<int:batch_id>/users/', views.batch_users, name='batch_users'),
    path('batches/<int:batch_id>/trainers/', views.batch_trainers, name='batch_trainers'),

    # Events
    path('events/', views.manage_events, name='manage_events'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:event_id>/participants/', views.event_participants, name='event_participants'),

    # Plans
    path('plans/', views.manage_plans, name='manage_plans'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:plan_id>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:plan_id>/delete/', views.plan_delete, name='plan_delete'),

    # Payments
    path('payments/', views.payment_reports, name='payment_reports'),
    path('payments/<int:payment_id>/status/', views.payment_status, name='payment_status'),
    path('due-payments/', views.due_payments, name='due_payments'),
    path('due-payments/remind/', views.due_remind, name='due_remind'),

    # Feedback & logs & settings
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('feedback/<int:feedback_id>/respond/', views.feedback_respond, name='feedback_respond'),
    path('logs/', views.activity_logs, name='activity_logs'),
    path('settings/', views.admin_settings, name='admin_settings'),
]