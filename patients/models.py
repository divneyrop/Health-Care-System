import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models


MRN_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
MRN_RANDOM_LENGTH = 12


def generate_medical_record_number():
    random_part = ''.join(
        secrets.choice(MRN_ALPHABET) for _ in range(MRN_RANDOM_LENGTH)
    )
    return f'CW-{random_part}'


class Patient(models.Model):
    class ContactType(models.TextChoices):
        PHONE = 'PHONE', 'Phone'
        EMAIL = 'EMAIL', 'Email'

    medical_record_number = models.CharField(
        max_length=15,
        unique=True,
        editable=False,
    )
    full_legal_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    registered_contact_type = models.CharField(
        max_length=5,
        choices=ContactType.choices,
    )
    registered_contact = models.CharField(max_length=254)
    portal_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='patient_record',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    registered_contact_type__in=('PHONE', 'EMAIL')
                ),
                name='patient_contact_type_valid',
            ),
            models.CheckConstraint(
                condition=~models.Q(registered_contact=''),
                name='patient_registered_contact_not_empty',
            ),
        ]

    def clean(self):
        super().clean()
        if self.registered_contact_type == self.ContactType.EMAIL:
            validate_email(self.registered_contact)
        if (
            self.portal_account_id
            and self.portal_account.role != get_user_model().Role.PATIENT
        ):
            raise ValidationError(
                {
                    'portal_account':
                    'A patient record can only link to a patient account.'
                }
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.medical_record_number = generate_medical_record_number()
        else:
            existing_mrn = type(self).objects.filter(pk=self.pk).values_list(
                'medical_record_number',
                flat=True,
            ).first()
            if (
                existing_mrn is not None
                and self.medical_record_number != existing_mrn
            ):
                raise ValidationError(
                    {
                        'medical_record_number':
                        'The medical record number is immutable.'
                    }
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.medical_record_number
