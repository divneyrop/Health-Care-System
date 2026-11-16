from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import PatientRegistrationForm


def home(request):
    return render(request, 'home.html')


def register(request):
    valid_roles = {'PATIENT', 'DOCTOR', 'STAFF'}
    selected_role = request.GET.get('role', '').upper()
    if request.method == 'POST':
        selected_role = request.POST.get('role', '').upper()

    if selected_role not in valid_roles:
        selected_role = ''

    if request.method == 'POST' and selected_role == 'PATIENT':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Your account has been created successfully. You can now log in.'
            )
            return redirect('registration:login')
    else:
        form = PatientRegistrationForm()
        if request.method == 'POST':
            messages.error(
                request,
                'Doctor and staff accounts are created by your organization’s Carewell administrator.'
            )

    return render(
        request,
        'registration/registration.html',
        {'form': form, 'selected_role': selected_role}
    )
