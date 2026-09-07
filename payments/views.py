from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from payments.models import MembershipPlan, Payment, PaymentAlert


@login_required
def plans(request):
    plans = MembershipPlan.objects.filter(is_active=True)
    return render(request, 'payments/plans.html', {'plans': plans})


@login_required
def payments(request):
    items = Payment.objects.filter(user=request.user).order_by('-payment_date')
    return render(request, 'payments/payments.html', {'items': items})


@login_required
def alerts(request):
    items = PaymentAlert.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/alerts.html', {'items': items})
