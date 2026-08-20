from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from books.models import Book, Edition
from shelf.models import ShelfItem

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class ShelfTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)

        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru',
            publishing_year=2007, accent_color='#2E1F14',
        )
        cls.edition = Edition.objects.create(
            book=cls.book, isbn='978-1-0000-0001-1',
            published_year=2020, price=Decimal('350.00'),
        )
        cls.other_edition = Edition.objects.create(
            book=cls.book, format=Edition.Format.SOFT, isbn='978-1-0000-0002-2',
            published_year=2022, price=Decimal('210.00'),
        )

    def test_add_edition_to_own_shelf(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/shelf/', {'edition_id': self.edition.id})
        self.assertEqual(response.status_code, 201)

        body = response.json()
        self.assertEqual(body['status'], 'want')
        self.assertFalse(body['is_owned'])
        self.assertEqual(body['edition']['book_name'], 'Имя ветра')
        self.assertEqual(body['edition']['accent_color'], '#2E1F14')

    def test_shelf_requires_authentication(self):
        self.assertEqual(self.client.get('/api/shelf/').status_code, 401)

    def test_same_edition_cannot_be_added_twice(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/shelf/', {'edition_id': self.edition.id})
        second = self.client.post('/api/shelf/', {'edition_id': self.edition.id})
        self.assertEqual(second.status_code, 400)
        self.assertIn('edition_id', second.json())

    def test_shelf_shows_only_own_items(self):
        ShelfItem.objects.create(user=self.alice, edition=self.edition)
        ShelfItem.objects.create(user=self.bob, edition=self.other_edition)

        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/shelf/')
        self.assertEqual(response.json()['count'], 1)

    def test_cannot_touch_someone_elses_item_by_id(self):
        item = ShelfItem.objects.create(user=self.bob, edition=self.edition)
        self.client.force_authenticate(user=self.alice)

        self.assertEqual(
            self.client.get('/api/shelf/{}/'.format(item.id)).status_code, 404,
        )
        self.assertEqual(
            self.client.delete('/api/shelf/{}/'.format(item.id)).status_code, 404,
        )
        self.assertTrue(ShelfItem.objects.filter(pk=item.pk).exists())

    def test_marking_as_read_sets_finished_at_and_progress(self):
        item = ShelfItem.objects.create(user=self.alice, edition=self.edition)
        self.client.force_authenticate(user=self.alice)

        response = self.client.patch('/api/shelf/{}/'.format(item.id), {'status': 'read'})
        self.assertEqual(response.status_code, 200)

        item.refresh_from_db()
        self.assertEqual(item.status, ShelfItem.Status.READ)
        self.assertEqual(item.progress_percent, 100)
        self.assertIsNotNone(item.finished_at)

    def test_reverting_status_clears_finished_at(self):
        item = ShelfItem.objects.create(user=self.alice, edition=self.edition)
        self.client.force_authenticate(user=self.alice)
        self.client.patch('/api/shelf/{}/'.format(item.id), {'status': 'read'})
        self.client.patch('/api/shelf/{}/'.format(item.id), {'status': 'reading'})

        item.refresh_from_db()
        self.assertIsNone(item.finished_at)

    def test_is_owned_cannot_be_set_by_client(self):
        """Иначе платный контент открывался бы обычным PATCH."""
        item = ShelfItem.objects.create(user=self.alice, edition=self.edition)
        self.client.force_authenticate(user=self.alice)

        response = self.client.patch('/api/shelf/{}/'.format(item.id), {'is_owned': True})
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertFalse(item.is_owned)

    def test_progress_is_validated(self):
        item = ShelfItem.objects.create(user=self.alice, edition=self.edition)
        self.client.force_authenticate(user=self.alice)
        response = self.client.patch('/api/shelf/{}/'.format(item.id), {'progress_percent': 150})
        self.assertEqual(response.status_code, 400)

    def test_filter_by_status(self):
        ShelfItem.objects.create(user=self.alice, edition=self.edition, status=ShelfItem.Status.READ)
        ShelfItem.objects.create(user=self.alice, edition=self.other_edition)

        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get('/api/shelf/?status=read').json()['count'], 1)


class PublicShelfTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)

        book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )
        cls.edition = Edition.objects.create(
            book=book, isbn='978-1-0000-0003-3',
            published_year=2020, price=Decimal('350.00'),
        )
        ShelfItem.objects.create(user=cls.alice, edition=cls.edition)

    def test_public_shelf_is_visible_to_anyone(self):
        response = self.client.get('/api/shelf/users/{}/'.format(self.alice.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_private_shelf_is_hidden_from_others(self):
        self.alice.is_shelf_public = False
        self.alice.save()

        anon = self.client.get('/api/shelf/users/{}/'.format(self.alice.id))
        self.assertEqual(anon.status_code, 403)

        self.client.force_authenticate(user=self.bob)
        stranger = self.client.get('/api/shelf/users/{}/'.format(self.alice.id))
        self.assertEqual(stranger.status_code, 403)

    def test_owner_still_sees_own_private_shelf(self):
        self.alice.is_shelf_public = False
        self.alice.save()

        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/shelf/users/{}/'.format(self.alice.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_unknown_user_returns_404(self):
        self.assertEqual(self.client.get('/api/shelf/users/999999/').status_code, 404)
