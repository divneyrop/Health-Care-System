from django.contrib.auth.forms import UserCreationForm

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
