from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Patient


User = get_user_model()


class PatientModelTests(TestCase):
    def create_patient(self, **overrides):
        values = {
            'full_legal_name': 'Test Patient',
            'date_of_birth': date(1990, 1, 1),
            'registered_contact_type': Patient.ContactType.EMAIL,
            'registered_contact': 'patient@example.test',
        }
        values.update(overrides)
        return Patient.objects.create(**values)

    def test_mrn_is_generated_as_an_opaque_unique_identifier(self):
        first = self.create_patient()
        second = self.create_patient(registered_contact='other@example.test')

        self.assertRegex(
            first.medical_record_number,
            r'^CW-[0-9A-HJKMNP-TV-Z]{12}$',
        )
        self.assertNotEqual(
            first.medical_record_number,
            second.medical_record_number,
        )

    def test_patient_supplied_mrn_is_not_used(self):
        patient = self.create_patient(medical_record_number='MRN-USER-SUPPLIED')

        self.assertRegex(
            patient.medical_record_number,
            r'^CW-[0-9A-HJKMNP-TV-Z]{12}$',
        )

    def test_patient_account_link_is_optional_and_patient_record_survives_account_delete(self):
        patient = self.create_patient()
        self.assertIsNone(patient.portal_account)

        account = User.objects.create_user(
            username='linked-patient',
            email='linked-patient@example.test',
            password='test-pass',
            role=User.Role.PATIENT,
        )
        patient.portal_account = account
        patient.save()

        account.delete()
        patient.refresh_from_db()

        self.assertIsNone(patient.portal_account)
        self.assertTrue(Patient.objects.filter(pk=patient.pk).exists())

    def test_patient_record_cannot_link_to_a_non_patient_account(self):
        account = User.objects.create_user(
            username='doctor-account',
            email='doctor@example.test',
            password='test-pass',
            role=User.Role.DOCTOR,
        )
        patient = Patient(
            medical_record_number='CW-0123456789AB',
            full_legal_name='Test Patient',
            date_of_birth=date(1990, 1, 1),
            registered_contact_type=Patient.ContactType.EMAIL,
            registered_contact='patient@example.test',
            portal_account=account,
        )

        with self.assertRaises(ValidationError):
            patient.full_clean()

    def test_portal_account_link_is_unique(self):
        account = User.objects.create_user(
            username='single-patient-account',
            email='single-patient@example.test',
            password='test-pass',
            role=User.Role.PATIENT,
        )
        self.create_patient(portal_account=account)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                second = self.create_patient(registered_contact='second@example.test')
                Patient.objects.filter(pk=second.pk).update(portal_account=account)

    def test_patient_mrn_cannot_be_changed_after_creation(self):
        patient = self.create_patient()
        patient.medical_record_number = 'CW-0123456789AB'

        with self.assertRaises(ValidationError):
            patient.save()
