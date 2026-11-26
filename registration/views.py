from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import AuthorizedHospitalCredential, User
from .forms import DoctorRegistrationForm, PatientRegistrationForm, StaffRegistrationForm


class RoleBasedLoginView(auth_views.LoginView):
    def get_default_redirect_url(self):
        if self.request.user.role == User.Role.PATIENT:
            return reverse('patients:dashboard')
        if self.request.user.role == User.Role.DOCTOR:
            return reverse('doctors:dashboard')
        if self.request.user.role == User.Role.STAFF:
            return reverse('hospital_staff:dashboard')
        return super().get_default_redirect_url()


def home(request):
    return render(request, 'home.html')

ROLE_FORMS = {
    'PATIENT': PatientRegistrationForm,
    'DOCTOR': DoctorRegistrationForm,
    'STAFF': StaffRegistrationForm,
}


class CredentialAlreadyRedeemed(Exception):
    pass


def _save_registration(form, selected_role):
    """Create the account and consume its professional credential atomically."""
    with transaction.atomic():
        user = form.save()

        if selected_role in ('DOCTOR', 'STAFF'):
            credential_field = 'doctor_id' if selected_role == 'DOCTOR' else 'staff_id'
            credential_type = (
                AuthorizedHospitalCredential.CredentialType.DOCTOR
                if selected_role == 'DOCTOR'
                else AuthorizedHospitalCredential.CredentialType.STAFF
            )
            credential_code = form.cleaned_data[credential_field]
            claimed = AuthorizedHospitalCredential.objects.filter(
                credential_type=credential_type,
                credential_code=credential_code,
                is_active=True,
                redeemed_at__isnull=True,
            ).update(redeemed_by=user, redeemed_at=timezone.now())

            if claimed != 1:
                raise CredentialAlreadyRedeemed

        return user


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
                try:
                    _save_registration(form, selected_role)
                except CredentialAlreadyRedeemed:
                    credential_field = (
                        'doctor_id' if selected_role == 'DOCTOR' else 'staff_id'
                    )
                    form.add_error(
                        credential_field,
                        'This credential has already been used or is no longer active. '
                        'Please contact the hospital for assistance.',
                    )
                else:
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
