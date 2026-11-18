import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .models import AuthorizedHospitalCredential


class SeedHospitalCredentialsTests(TestCase):
    def write_csv(self, content):
        temporary_directory = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent
        )
        self.addCleanup(temporary_directory.cleanup)
        csv_path = Path(temporary_directory.name) / 'credentials.csv'
        csv_path.write_text(content, encoding='utf-8')
        return csv_path

    def test_seed_command_is_idempotent_and_preserves_existing_state(self):
        existing = AuthorizedHospitalCredential.objects.create(
            credential_type=AuthorizedHospitalCredential.CredentialType.DOCTOR,
            credential_code='DOC-100',
            is_active=False,
        )
        csv_path = self.write_csv(
            'credential_type,credential_code\n'
            ' doctor , doc-100 \n'
            'STAFF,STAFF-200\n'
        )

        call_command('seed_hospital_credentials', csv_path=str(csv_path), verbosity=0)
        call_command('seed_hospital_credentials', csv_path=str(csv_path), verbosity=0)

        self.assertEqual(AuthorizedHospitalCredential.objects.count(), 2)
        existing.refresh_from_db()
        self.assertFalse(existing.is_active)
        self.assertTrue(
            AuthorizedHospitalCredential.objects.filter(
                credential_type=AuthorizedHospitalCredential.CredentialType.STAFF,
                credential_code='STAFF-200',
            ).exists()
        )

    def test_invalid_file_is_rejected_before_any_credentials_are_added(self):
        csv_path = self.write_csv(
            'credential_type,credential_code\n'
            'PATIENT,patient-code\n'
        )

        with self.assertRaises(CommandError):
            call_command(
                'seed_hospital_credentials', csv_path=str(csv_path), verbosity=0
            )

        self.assertEqual(AuthorizedHospitalCredential.objects.count(), 0)
