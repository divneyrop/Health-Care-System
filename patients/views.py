from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Patient


@login_required
def dashboard(request):
    if request.user.role != 'PATIENT':
        messages.info(
            request,
            'The patient dashboard is available to patient accounts.',
        )
        return redirect('registration:home')

    patient_record = Patient.objects.filter(portal_account=request.user).first()
    return render(
        request,
        'patients/dashboard.html',
        {'patient_record': patient_record},
    )


@login_required
def profile(request):
    if request.user.role != 'PATIENT':
        messages.info(
            request,
            'The patient profile is available to patient accounts.',
        )
        return redirect('registration:home')

    patient_record = Patient.objects.filter(portal_account=request.user).first()
    return render(
        request,
        'patients/profile.html',
        {'patient_record': patient_record},
    )
