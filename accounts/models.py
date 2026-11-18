from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'
        STAFF = 'STAFF', 'Staff'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT
    )

    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuthorizedHospitalCredential(models.Model):
    """Hospital-issued credential that permits a professional to register."""

    class CredentialType(models.TextChoices):
        DOCTOR = 'DOCTOR', 'Doctor'
        STAFF = 'STAFF', 'Staff'

    credential_type = models.CharField(max_length=10, choices=CredentialType.choices)
    credential_code = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('credential_type', 'credential_code'),
                name='unique_hospital_credential_by_type',
            ),
        ]
        ordering = ('credential_type', 'credential_code')

    def save(self, *args, **kwargs):
        self.credential_code = self.credential_code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_credential_type_display()} credential: {self.credential_code}'
