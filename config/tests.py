from django.test import Client, TestCase
from django.urls import reverse


class CsrfFailureViewTests(TestCase):
    def test_invalid_csrf_request_shows_carewell_error_page(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(reverse('registration:login'), {})

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'errors/csrf_failure.html')
        self.assertContains(
            response,
            'We couldn’t verify this request.',
            status_code=403,
        )
        self.assertContains(
            response,
            reverse('registration:home'),
            status_code=403,
        )
        self.assertContains(
            response,
            reverse('registration:login'),
            status_code=403,
        )
        self.assertNotContains(
            response,
            'CSRF token missing or incorrect',
            status_code=403,
        )
