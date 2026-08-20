from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class RegistrationTests(APITestCase):
    def test_register_creates_customer(self):
        response = self.client.post('/api/accounts/register/', {
            'username': 'newreader', 'email': 'new@example.com',
            'password': PASSWORD, 'password2': PASSWORD,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('password', response.json())
        self.assertEqual(User.objects.get(username='newreader').role, 'customer')

    def test_role_cannot_be_set_at_registration(self):
        """Раньше role принималась от клиента — можно было зарегистрироваться админом."""
        response = self.client.post('/api/accounts/register/', {
            'username': 'hacker', 'email': 'h@example.com', 'role': 'admin',
            'password': PASSWORD, 'password2': PASSWORD,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='hacker')
        self.assertEqual(user.role, 'customer')
        self.assertFalse(user.is_staff)

    def test_password_mismatch_is_rejected(self):
        response = self.client.post('/api/accounts/register/', {
            'username': 'sloppy', 'email': 's@example.com',
            'password': PASSWORD, 'password2': 'somethingelse',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password2', response.json())

    def test_weak_password_is_rejected(self):
        response = self.client.post('/api/accounts/register/', {
            'username': 'weak', 'email': 'w@example.com',
            'password': '12345', 'password2': '12345',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username='first', email='taken@example.com', password=PASSWORD)
        response = self.client.post('/api/accounts/register/', {
            'username': 'second', 'email': 'TAKEN@example.com',
            'password': PASSWORD, 'password2': PASSWORD,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())


class AuthFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='reader', email='r@example.com', password=PASSWORD,
        )

    def test_token_obtain_then_me(self):
        token_response = self.client.post('/api/accounts/token/', {
            'username': 'reader', 'password': PASSWORD,
        }, format='json')
        self.assertEqual(token_response.status_code, 200)

        access = token_response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access))

        me = self.client.get('/api/accounts/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['username'], 'reader')

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get('/api/accounts/me/').status_code, 401)

    def test_me_cannot_self_promote_to_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch('/api/accounts/me/', {'role': 'admin', 'bio': 'Читаю фэнтези.'})
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'customer')
        self.assertEqual(self.user.bio, 'Читаю фэнтези.')

    def test_logout_blacklists_refresh_token(self):
        tokens = self.client.post('/api/accounts/token/', {
            'username': 'reader', 'password': PASSWORD,
        }, format='json').json()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(tokens['access']))

        logout = self.client.post(
            '/api/accounts/logout/', {'refresh': tokens['refresh']}, format='json',
        )
        self.assertEqual(logout.status_code, 205)

        reuse = self.client.post(
            '/api/accounts/token/refresh/', {'refresh': tokens['refresh']}, format='json',
        )
        self.assertEqual(reuse.status_code, 401)

    def test_logout_without_refresh_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/accounts/logout/', {}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_logout_with_garbage_token_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/accounts/logout/', {'refresh': 'not-a-token'}, format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_public_profile_hides_private_fields(self):
        response = self.client.get('/api/accounts/users/{}/'.format(self.user.id))
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body['username'], 'reader')
        self.assertNotIn('email', body)
        self.assertNotIn('password', body)
        self.assertNotIn('phone', body)
