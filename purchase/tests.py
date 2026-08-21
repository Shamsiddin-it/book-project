import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from rest_framework.test import APITestCase

from books.models import Book, Edition
from purchase.models import CartItem, Order, OrderItem
from shelf.models import ShelfItem

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class PurchaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)

        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )
        cls.hardcover = Edition.objects.create(
            book=cls.book, format=Edition.Format.HARD, isbn='978-1-0000-0001-1',
            published_year=2020, price=Decimal('350.00'),
        )
        cls.ebook = Edition.objects.create(
            book=cls.book, format=Edition.Format.EBOOK, isbn='978-1-0000-0002-2',
            published_year=2022, price=Decimal('210.00'),
        )


class CartTests(PurchaseTestCase):
    def test_add_and_list(self):
        self.client.force_authenticate(user=self.alice)

        response = self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.assertEqual(response.status_code, 201)

        listing = self.client.get('/api/purchase/cart/')
        self.assertEqual(listing.status_code, 200)
        body = listing.json()
        self.assertEqual(body['count'], 1)
        self.assertEqual(Decimal(body['total']), Decimal('210.00'))
        self.assertTrue(body['purchases_are_free'])

    def test_cart_requires_authentication(self):
        self.assertEqual(self.client.get('/api/purchase/cart/').status_code, 401)

    def test_same_edition_cannot_be_added_twice(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        second = self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.assertEqual(second.status_code, 400)

    def test_owned_edition_cannot_be_added(self):
        ShelfItem.objects.create(user=self.alice, edition=self.ebook, is_owned=True)

        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.assertEqual(response.status_code, 400)

    def test_cart_is_per_user(self):
        CartItem.objects.create(user=self.bob, edition=self.ebook)

        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get('/api/purchase/cart/').json()['count'], 0)

    def test_cannot_delete_someone_elses_cart_item(self):
        item = CartItem.objects.create(user=self.bob, edition=self.ebook)

        self.client.force_authenticate(user=self.alice)
        response = self.client.delete('/api/purchase/cart/{}/'.format(item.id))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_inactive_edition_cannot_be_added(self):
        self.ebook.is_active = False
        self.ebook.save()

        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.assertEqual(response.status_code, 400)


class CheckoutTests(PurchaseTestCase):
    def test_checkout_grants_ownership_for_free(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.client.post('/api/purchase/cart/', {'edition_id': self.hardcover.id})

        response = self.client.post('/api/purchase/checkout/')
        self.assertEqual(response.status_code, 201)

        body = response.json()
        self.assertEqual(body['status'], 'paid')
        self.assertEqual(body['provider'], 'free')
        self.assertTrue(body['is_free'])
        # Сумма по прайсу сохраняется, а денег не взято.
        self.assertEqual(Decimal(body['total']), Decimal('560.00'))
        self.assertEqual(Decimal(body['amount_paid']), Decimal('0.00'))
        self.assertEqual(len(body['items']), 2)

        owned = ShelfItem.objects.filter(user=self.alice, is_owned=True)
        self.assertEqual(owned.count(), 2)

    def test_checkout_empties_the_cart(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.client.post('/api/purchase/checkout/')

        self.assertEqual(CartItem.objects.filter(user=self.alice).count(), 0)

    def test_empty_cart_is_rejected(self):
        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.post('/api/purchase/checkout/').status_code, 400)

    def test_checkout_requires_authentication(self):
        self.assertEqual(self.client.post('/api/purchase/checkout/').status_code, 401)

    def test_existing_shelf_item_keeps_its_progress(self):
        """Книга уже лежала как «хочу прочитать» — покупка не должна сбросить статус."""
        item = ShelfItem.objects.create(
            user=self.alice, edition=self.ebook,
            status=ShelfItem.Status.READING, progress_percent=40,
        )

        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.client.post('/api/purchase/checkout/')

        item.refresh_from_db()
        self.assertTrue(item.is_owned)
        self.assertEqual(item.status, ShelfItem.Status.READING)
        self.assertEqual(item.progress_percent, 40)

    def test_price_is_frozen_in_order_history(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})
        self.client.post('/api/purchase/checkout/')

        self.ebook.price = Decimal('999.00')
        self.ebook.save()

        item = OrderItem.objects.get(edition=self.ebook)
        self.assertEqual(item.unit_price, Decimal('210.00'))

    @override_settings(PURCHASES_ARE_FREE=False)
    def test_with_payments_enabled_order_stays_pending(self):
        """Флаг выключен — заказ создаётся, но доступ без оплаты не выдаётся."""
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/cart/', {'edition_id': self.ebook.id})

        response = self.client.post('/api/purchase/checkout/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'pending')

        self.assertFalse(
            ShelfItem.objects.filter(user=self.alice, edition=self.ebook, is_owned=True).exists()
        )
        # Корзина не очищается — оформление ещё не завершено.
        self.assertEqual(CartItem.objects.filter(user=self.alice).count(), 1)


_TEMP_PROTECTED_ROOT = tempfile.mkdtemp(prefix='protected-media-purchase-')


@override_settings(PROTECTED_MEDIA_ROOT=_TEMP_PROTECTED_ROOT)
class AcquireTests(PurchaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, _TEMP_PROTECTED_ROOT, True)

    def test_one_click_acquire(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            '/api/purchase/editions/{}/acquire/'.format(self.ebook.id)
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'paid')

        self.assertTrue(
            ShelfItem.objects.filter(user=self.alice, edition=self.ebook, is_owned=True).exists()
        )

    def test_acquiring_twice_is_rejected(self):
        self.client.force_authenticate(user=self.alice)
        url = '/api/purchase/editions/{}/acquire/'.format(self.ebook.id)

        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertEqual(Order.objects.filter(user=self.alice).count(), 1)

    def test_acquire_requires_authentication(self):
        response = self.client.post(
            '/api/purchase/editions/{}/acquire/'.format(self.ebook.id)
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_edition_returns_404(self):
        self.ebook.is_active = False
        self.ebook.save()

        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            '/api/purchase/editions/{}/acquire/'.format(self.ebook.id)
        )
        self.assertEqual(response.status_code, 404)

    def test_acquired_book_becomes_readable(self):
        """Смысл всей бесплатной выдачи: после неё ридер открывает книгу."""
        self.ebook.file.save('book.pdf', ContentFile(b'fake book text'))

        self.client.force_authenticate(user=self.alice)
        before = self.client.get('/api/reader/{}/'.format(self.ebook.id))
        self.assertEqual(before.status_code, 403)

        self.client.post('/api/purchase/editions/{}/acquire/'.format(self.ebook.id))

        after = self.client.get('/api/reader/{}/'.format(self.ebook.id))
        self.assertEqual(after.status_code, 200)

        content = self.client.get('/api/reader/{}/content/'.format(self.ebook.id))
        self.assertEqual(content.status_code, 200)


class OrderHistoryTests(PurchaseTestCase):
    def test_history_shows_only_own_orders(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/purchase/editions/{}/acquire/'.format(self.ebook.id))

        self.client.force_authenticate(user=self.bob)
        self.client.post('/api/purchase/editions/{}/acquire/'.format(self.hardcover.id))

        response = self.client.get('/api/purchase/orders/')
        self.assertEqual(response.json()['count'], 1)

    def test_cannot_read_someone_elses_order(self):
        self.client.force_authenticate(user=self.alice)
        order_id = self.client.post(
            '/api/purchase/editions/{}/acquire/'.format(self.ebook.id)
        ).json()['id']

        self.client.force_authenticate(user=self.bob)
        response = self.client.get('/api/purchase/orders/{}/'.format(order_id))
        self.assertEqual(response.status_code, 404)

    def test_history_requires_authentication(self):
        self.assertEqual(self.client.get('/api/purchase/orders/').status_code, 401)
