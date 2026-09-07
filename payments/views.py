from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def plans(request):
    return redirect('user_payments')


@login_required
def payments(request):
    return redirect('user_payments')


@login_required
def alerts(request):
    return redirect('user_payments')