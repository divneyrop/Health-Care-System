from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import DoctorRegistrationForm, PatientRegistrationForm, StaffRegistrationForm


def home(request):
    return render(request, 'home.html')

ROLE_FORMS = {
    'PATIENT': PatientRegistrationForm,
    'DOCTOR': DoctorRegistrationForm,
    'STAFF': StaffRegistrationForm,
}


def register(request):

    selected_role = request.GET.get('role', '').upper()

    if request.method == 'POST':
        selected_role = request.POST.get('role', '').upper()

    form_class = ROLE_FORMS.get(selected_role)

    form = None

    if form_class:

        if request.method == 'POST':
            form = form_class(request.POST)

            if form.is_valid():
                form.save()

                messages.success(
                    request,
                    'Your account has been created successfully. You can now log in.'
                )

                return redirect('registration:login')

        else:
            form = form_class()

    return render(
        request,
        'registration/registration.html',
        {
            'form': form,
            'selected_role': selected_role,
        }
    )
