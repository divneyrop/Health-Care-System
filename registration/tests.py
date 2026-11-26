from django.test import TestCase
from django.urls import reverse

from accounts.models import AuthorizedHospitalCredential, User


class RegistrationCredentialTests(TestCase):
    def setUp(self):
        self.doctor_credential = AuthorizedHospitalCredential.objects.create(
            credential_type=AuthorizedHospitalCredential.CredentialType.DOCTOR,
            credential_code='DOC-100',
        )
        self.staff_credential = AuthorizedHospitalCredential.objects.create(
            credential_type=AuthorizedHospitalCredential.CredentialType.STAFF,
            credential_code='STAFF-100',
        )

    def registration_data(self, role, username, **extra):
        data = {
            'role': role,
            'first_name': 'Test',
            'last_name': 'User',
            'username': username,
            'email': f'{username}@example.test',
            'password1': 'Carewell-test-Pass-482!',
            'password2': 'Carewell-test-Pass-482!',
        }
        data.update(extra)
        return data

    def test_patient_registration_needs_no_hospital_credential(self):
        response = self.client.post(
            reverse('registration:register'),
            self.registration_data('PATIENT', 'patient-new'),
        )

        self.assertRedirects(response, reverse('registration:login'))
        user = User.objects.get(username='patient-new')
        self.assertEqual(user.role, User.Role.PATIENT)
        self.doctor_credential.refresh_from_db()
        self.staff_credential.refresh_from_db()
        self.assertIsNone(self.doctor_credential.redeemed_at)
        self.assertIsNone(self.staff_credential.redeemed_at)

    def test_doctor_registration_normalizes_and_redeems_credential(self):
        response = self.client.post(
            reverse('registration:register'),
            self.registration_data('DOCTOR', 'doctor-new', doctor_id=' doc-100 '),
        )

        self.assertRedirects(response, reverse('registration:login'))
        user = User.objects.get(username='doctor-new')
        self.assertEqual(user.role, User.Role.DOCTOR)
        self.doctor_credential.refresh_from_db()
        self.assertEqual(self.doctor_credential.redeemed_by, user)
        self.assertIsNotNone(self.doctor_credential.redeemed_at)

    def test_staff_registration_redeems_staff_credential(self):
        response = self.client.post(
            reverse('registration:register'),
            self.registration_data('STAFF', 'staff-new', staff_id='staff-100'),
        )

        self.assertRedirects(response, reverse('registration:login'))
        user = User.objects.get(username='staff-new')
        self.assertEqual(user.role, User.Role.STAFF)
        self.staff_credential.refresh_from_db()
        self.assertEqual(self.staff_credential.redeemed_by, user)

    def test_doctor_cannot_use_staff_credential(self):
        response = self.client.post(
            reverse('registration:register'),
            self.registration_data('DOCTOR', 'wrong-role', doctor_id='STAFF-100'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('doctor_id', response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='wrong-role').exists())
        self.assertIsNone(self.staff_credential.redeemed_at)

    def test_inactive_credential_cannot_create_professional_account(self):
        self.doctor_credential.is_active = False
        self.doctor_credential.save(update_fields=('is_active',))

        response = self.client.post(
            reverse('registration:register'),
            self.registration_data('DOCTOR', 'inactive-credential', doctor_id='DOC-100'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('doctor_id', response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='inactive-credential').exists())

    def test_credential_cannot_create_a_second_professional_account(self):
        first_response = self.client.post(
            reverse('registration:register'),
            self.registration_data('DOCTOR', 'doctor-first', doctor_id='DOC-100'),
        )
        self.assertRedirects(first_response, reverse('registration:login'))

        second_response = self.client.post(
            reverse('registration:register'),
            self.registration_data('DOCTOR', 'doctor-second', doctor_id='DOC-100'),
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn('doctor_id', second_response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='doctor-second').exists())
        self.assertEqual(User.objects.filter(role=User.Role.DOCTOR).count(), 1)

    def test_existing_doctor_and_staff_accounts_remain_unchanged(self):
        existing_doctor = User.objects.create_user(
            username='legacy-doctor',
            email='legacy-doctor@example.test',
            password='Existing-test-Pass-482!',
            role=User.Role.DOCTOR,
        )
        existing_staff = User.objects.create_user(
            username='legacy-staff',
            email='legacy-staff@example.test',
            password='Existing-test-Pass-482!',
            role=User.Role.STAFF,
            is_staff=True,
        )

        response = self.client.post(
            reverse('registration:register'),
            self.registration_data('PATIENT', 'patient-preserves-legacy'),
        )

        self.assertRedirects(response, reverse('registration:login'))
        existing_doctor.refresh_from_db()
        existing_staff.refresh_from_db()
        self.assertEqual(existing_doctor.role, User.Role.DOCTOR)
        self.assertTrue(existing_doctor.is_active)
        self.assertEqual(existing_staff.role, User.Role.STAFF)
        self.assertTrue(existing_staff.is_staff)
        self.assertTrue(existing_staff.is_active)

    def test_doctor_sign_in_redirects_to_doctor_dashboard(self):
        User.objects.create_user(
            username='doctor-login',
            email='doctor-login@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.DOCTOR,
        )

        response = self.client.post(
            reverse('registration:login'),
            {
                'username': 'doctor-login',
                'password': 'Carewell-test-Pass-482!',
            },
        )

        self.assertRedirects(response, reverse('doctors:dashboard'))
        self.assertContains(
            self.client.get(reverse('doctors:dashboard')),
            'Care team workspace',
        )

    def test_patient_sign_in_redirects_to_patient_dashboard(self):
        User.objects.create_user(
            username='patient-login',
            email='patient-login@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.PATIENT,
        )

        response = self.client.post(
            reverse('registration:login'),
            {
                'username': 'patient-login',
                'password': 'Carewell-test-Pass-482!',
            },
        )

        self.assertRedirects(response, reverse('patients:dashboard'))
        self.assertContains(
            self.client.get(reverse('patients:dashboard')),
            'Patient workspace',
        )

    def test_staff_sign_in_redirects_to_staff_dashboard(self):
        User.objects.create_user(
            username='staff-login',
            email='staff-login@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.STAFF,
        )

        response = self.client.post(
            reverse('registration:login'),
            {
                'username': 'staff-login',
                'password': 'Carewell-test-Pass-482!',
            },
        )

        self.assertRedirects(response, reverse('hospital_staff:dashboard'))
        self.assertContains(
            self.client.get(reverse('hospital_staff:dashboard')),
            'Hospital workspace',
        )

    def test_anonymous_user_is_redirected_to_sign_in_before_doctor_dashboard(self):
        dashboard_url = reverse('doctors:dashboard')

        response = self.client.get(dashboard_url)

        self.assertRedirects(
            response,
            f'{reverse("registration:login")}?next={dashboard_url}',
        )
        self.assertContains(self.client.get(response.url), 'Sign in')

    def test_sign_in_preserves_requested_destination(self):
        User.objects.create_user(
            username='patient-next',
            email='patient-next@example.test',
            password='Carewell-test-Pass-482!',
            role=User.Role.PATIENT,
        )
        destination = reverse('patients:dashboard')

        response = self.client.post(
            f'{reverse("registration:login")}?next={destination}',
            {
                'username': 'patient-next',
                'password': 'Carewell-test-Pass-482!',
                'next': destination,
            },
        )

        self.assertRedirects(response, destination)


class SharedNavigationTests(TestCase):
    def test_public_navigation_marks_current_auth_action(self):
        home_response = self.client.get(reverse('registration:home'))
        self.assertContains(home_response, 'href="/" aria-current="page">Home</a>')
        self.assertContains(home_response, 'Sign in</a>')
        self.assertContains(home_response, 'Get started')

        login_response = self.client.get(reverse('registration:login'))
        self.assertContains(
            login_response,
            f'href="{reverse("registration:login")}" aria-current="page">Sign in</a>',
        )

        registration_response = self.client.get(reverse('registration:register'))
        self.assertContains(
            registration_response,
            f'href="{reverse("registration:register")}" aria-current="page">Get started',
        )

    def test_each_role_sees_its_dashboard_and_profile_navigation(self):
        dashboards = (
            (User.Role.PATIENT, 'patients:dashboard'),
            (User.Role.DOCTOR, 'doctors:dashboard'),
            (User.Role.STAFF, 'hospital_staff:dashboard'),
        )

        for index, (role, dashboard_name) in enumerate(dashboards):
            user = User.objects.create_user(
                username=f'nav-user-{index}',
                email=f'nav-user-{index}@example.test',
                password='Carewell-test-Pass-482!',
                role=role,
            )
            self.client.force_login(user)
            dashboard_url = reverse(dashboard_name)
            response = self.client.get(dashboard_url)

            self.assertContains(
                response,
                f'href="{dashboard_url}" aria-current="page">Dashboard</a>',
            )
            profile_label = 'My profile' if role == User.Role.PATIENT else 'Profile'
            self.assertContains(
                response,
                f'href="{dashboard_url}#account">{profile_label}</a>',
            )
            self.assertContains(response, 'Sign out')
            self.assertNotContains(response, 'Get started')
            self.assertNotContains(response, 'My account')
