from django.contrib.auth.models import User
from django.db import models


class MembershipPlan(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_in_months = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [('Paid', 'Paid'), ('Pending', 'Pending'), ('Overdue', 'Overdue')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    membership_plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    payment_month = models.CharField(max_length=20, blank=True)
    payment_year = models.CharField(max_length=10, blank=True)
    payment_method = models.CharField(max_length=100, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} - {self.amount}'


class PaymentAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_alerts')
    message = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Alert for {self.user.username}'
