from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

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


class PatientDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='portal-patient',
            first_name='Portal',
            last_name='Patient',
            email='portal-patient@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.PATIENT,
        )
        self.dashboard_url = reverse('patients:dashboard')
        self.profile_url = reverse('patients:profile')

    def create_patient_record(self, **overrides):
        values = {
            'full_legal_name': 'Portal Patient',
            'date_of_birth': date(1990, 1, 1),
            'registered_contact_type': Patient.ContactType.EMAIL,
            'registered_contact': 'portal-patient@example.test',
            'portal_account': self.user,
        }
        values.update(overrides)
        return Patient.objects.create(**values)

    def test_dashboard_links_to_a_separate_profile_page(self):
        own_record = self.create_patient_record()
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, Portal.')
        self.assertContains(response, 'View my profile')
        self.assertContains(response, f'href="{self.profile_url}"')
        self.assertNotContains(response, own_record.medical_record_number)

    def test_profile_shows_only_the_signed_in_patients_linked_record(self):
        own_record = self.create_patient_record()
        other_user = User.objects.create_user(
            username='another-patient',
            email='another-patient@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.PATIENT,
        )
        Patient.objects.create(
            full_legal_name='Another Patient Private Name',
            date_of_birth=date(1985, 5, 12),
            registered_contact_type=Patient.ContactType.PHONE,
            registered_contact='555-0101',
            portal_account=other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My profile')
        self.assertContains(response, 'Portal Patient')
        self.assertContains(response, own_record.medical_record_number)
        self.assertContains(response, 'Read-only')
        self.assertNotContains(response, 'Another Patient Private Name')
        self.assertNotContains(response, '555-0101')

    def test_dashboard_shows_clear_empty_state_when_no_record_is_linked(self):
        self.client.force_login(self.user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Care activity isn’t available here yet')
        self.assertContains(response, 'Account only')
        self.assertNotContains(response, 'No patient record is linked')

    def test_profile_shows_empty_state_when_no_record_is_linked(self):
        self.client.force_login(self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No patient record is linked')
        self.assertContains(response, 'portal-patient@example.test')
        self.assertNotContains(response, 'Medical record number')

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.dashboard_url)

        self.assertRedirects(
            response,
            f'{reverse("registration:login")}?next={self.dashboard_url}',
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(self.profile_url)

        self.assertRedirects(
            response,
            f'{reverse("registration:login")}?next={self.profile_url}',
        )

    def test_dashboard_rejects_non_patient_roles(self):
        doctor = User.objects.create_user(
            username='portal-doctor',
            email='portal-doctor@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.DOCTOR,
        )
        self.client.force_login(doctor)

        response = self.client.get(self.dashboard_url)

        self.assertRedirects(response, reverse('registration:home'))

    def test_profile_rejects_non_patient_roles(self):
        doctor = User.objects.create_user(
            username='profile-doctor',
            email='profile-doctor@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.DOCTOR,
        )
        self.client.force_login(doctor)

        response = self.client.get(self.profile_url)

        self.assertRedirects(response, reverse('registration:home'))

    def test_profile_navigation_marks_the_current_page(self):
        self.client.force_login(self.user)

        response = self.client.get(self.profile_url)

        self.assertContains(
            response,
            f'href="{self.profile_url}" aria-current="page">My profile</a>',
        )
        self.assertContains(response, f'href="{self.dashboard_url}">Dashboard</a>')
