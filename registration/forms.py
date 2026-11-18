from django.contrib.auth.forms import UserCreationForm
from django import forms

from accounts.models import AuthorizedHospitalCredential, User


class PatientRegistrationForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT

        if commit:
            user.save()

        return user

class DoctorRegistrationForm(UserCreationForm):
    doctor_id = forms.CharField(
        max_length=20,
        label='Hospital Doctor ID'
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
        ]

    def clean_doctor_id(self):
        doctor_id = self.cleaned_data['doctor_id'].strip().upper()
        authorized = AuthorizedHospitalCredential.objects.filter(
            credential_type=AuthorizedHospitalCredential.CredentialType.DOCTOR,
            credential_code=doctor_id,
            is_active=True,
            redeemed_at__isnull=True,
        ).exists()
        if not authorized:
            raise forms.ValidationError(
                'Enter a valid, active hospital doctor ID.'
            )
        return doctor_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DOCTOR

        if commit:
            user.save()

        return user

class StaffRegistrationForm(UserCreationForm):
    staff_id = forms.CharField(
        max_length=20,
        label='Hospital Staff ID'
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
        ]

    def clean_staff_id(self):
        staff_id = self.cleaned_data['staff_id'].strip().upper()
        authorized = AuthorizedHospitalCredential.objects.filter(
            credential_type=AuthorizedHospitalCredential.CredentialType.STAFF,
            credential_code=staff_id,
            is_active=True,
            redeemed_at__isnull=True,
        ).exists()
        if not authorized:
            raise forms.ValidationError(
                'Enter a valid, active hospital staff ID.'
            )
        return staff_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STAFF

        if commit:
            user.save()

        return user
