from django.urls import path

from . import views

urlpatterns = [
    path('plans/', views.plans, name='payments_plans'),
    path('payments/', views.payments, name='payments_history'),
    path('alerts/', views.alerts, name='payment_alerts'),
]
