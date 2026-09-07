from django.contrib import admin

from .models import MembershipPlan, Payment, PaymentAlert


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount', 'duration_in_months', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'membership_plan', 'amount', 'payment_date', 'payment_month', 'payment_year', 'status']
    search_fields = ['user__username', 'transaction_id']
    list_filter = ['status', 'payment_month', 'payment_year']


@admin.register(PaymentAlert)
class PaymentAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'due_date', 'is_read', 'created_at']
    list_filter = ['is_read']