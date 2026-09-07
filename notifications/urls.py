from django.urls import path

from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications_list'),
    path('feedback/', views.feedback_form, name='feedback_form'),
]
