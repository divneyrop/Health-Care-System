import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import AuthorizedHospitalCredential


class Command(BaseCommand):
    help = (
        'Add authorized hospital credentials from a CSV file with '
        'credential_type and credential_code columns.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            dest='csv_path',
            required=True,
            help='Path to a UTF-8 CSV containing credential_type,credential_code.',
        )

    def handle(self, *args, **options):
        path = Path(options['csv_path'])
        try:
            rows = self._read_credentials(path)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise CommandError(f'Unable to read credential CSV: {exc}') from exc

        created_count = 0
        with transaction.atomic():
            for credential_type, credential_code in rows:
                _, created = AuthorizedHospitalCredential.objects.get_or_create(
                    credential_type=credential_type,
                    credential_code=credential_code,
                )
                created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Credential seeding complete: {created_count} added, '
                f'{len(rows) - created_count} already present.'
            )
        )

    @staticmethod
    def _read_credentials(path):
        credentials = []
        seen = set()
        allowed_types = set(AuthorizedHospitalCredential.CredentialType.values)

        with path.open(newline='', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames != ['credential_type', 'credential_code']:
                raise CommandError(
                    'CSV must have exactly these headers: '
                    'credential_type,credential_code.'
                )

            for line_number, row in enumerate(reader, start=2):
                credential_type = (row.get('credential_type') or '').strip().upper()
                credential_code = (row.get('credential_code') or '').strip().upper()

                if not credential_type and not credential_code:
                    continue
                if credential_type not in allowed_types:
                    raise CommandError(
                        f'Invalid credential_type on CSV line {line_number}; '
                        'use DOCTOR or STAFF.'
                    )
                if not credential_code or len(credential_code) > 64:
                    raise CommandError(
                        f'credential_code on CSV line {line_number} must contain '
                        'between 1 and 64 characters.'
                    )

                credential = (credential_type, credential_code)
                if credential in seen:
                    raise CommandError(
                        f'Duplicate credential entry on CSV line {line_number}.'
                    )
                seen.add(credential)
                credentials.append(credential)

        if not credentials:
            raise CommandError('CSV contains no credential entries.')

        return credentials
