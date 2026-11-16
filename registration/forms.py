from django.contrib.auth.forms import UserCreationForm
from django import forms

from accounts.models import User


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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STAFF

        if commit:
            user.save()

        return user