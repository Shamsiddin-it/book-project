from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

from books.models import Book, Edition
from reviews.models import Review

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class ReviewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)
        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )

    def test_create_review_sets_author(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/reviews/', {
            'book': self.book.id, 'rating': 5, 'text': 'Прекрасно.',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['user']['username'], 'alice')

    def test_review_requires_authentication(self):
        response = self.client.post('/api/reviews/', {'book': self.book.id, 'rating': 5})
        self.assertEqual(response.status_code, 401)

    def test_rating_out_of_range_is_rejected(self):
        self.client.force_authenticate(user=self.alice)
        for bad in (0, 6, -1):
            response = self.client.post('/api/reviews/', {'book': self.book.id, 'rating': bad})
            self.assertEqual(response.status_code, 400, bad)

    def test_second_review_gives_form_error_not_crash(self):
        """Уникальность есть в БД, но клиент должен получить 400, а не 500."""
        Review.objects.create(user=self.alice, book=self.book, rating=4)

        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/reviews/', {'book': self.book.id, 'rating': 2})
        self.assertEqual(response.status_code, 400)
        self.assertIn('book', response.json())

    def test_duplicate_blocked_at_database_level(self):
        Review.objects.create(user=self.alice, book=self.book, rating=4)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(user=self.alice, book=self.book, rating=1)

    def test_author_can_edit_own_review(self):
        review = Review.objects.create(user=self.alice, book=self.book, rating=3)
        self.client.force_authenticate(user=self.alice)

        response = self.client.patch('/api/reviews/{}/'.format(review.id), {'rating': 5})
        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)

    def test_stranger_cannot_edit_review(self):
        review = Review.objects.create(user=self.alice, book=self.book, rating=3)
        self.client.force_authenticate(user=self.bob)

        self.assertEqual(
            self.client.patch('/api/reviews/{}/'.format(review.id), {'rating': 1}).status_code,
            403,
        )

    def test_text_is_optional(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/reviews/', {'book': self.book.id, 'rating': 4})
        self.assertEqual(response.status_code, 201)


class RatingSummaryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )
        for index, rating in enumerate([5, 5, 4, 3]):
            user = User.objects.create_user(username='reader{}'.format(index), password=PASSWORD)
            Review.objects.create(user=user, book=cls.book, rating=rating)

    def test_summary_reports_average_and_distribution(self):
        response = self.client.get('/api/reviews/books/{}/summary/'.format(self.book.id))
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body['average_rating'], 4.3)  # (5+5+4+3)/4 = 4.25 → 4.3
        self.assertEqual(body['reviews_count'], 4)
        self.assertEqual(body['distribution']['5'], 2)
        self.assertEqual(body['distribution']['1'], 0)

    def test_summary_for_book_without_reviews(self):
        empty = Book.objects.create(
            name='Без отзывов', description='.', language='ru', publishing_year=2000,
        )
        body = self.client.get('/api/reviews/books/{}/summary/'.format(empty.id)).json()
        self.assertIsNone(body['average_rating'])
        self.assertEqual(body['reviews_count'], 0)

    def test_catalog_exposes_average_rating(self):
        response = self.client.get('/api/books/')
        card = next(
            item for item in response.json()['results'] if item['id'] == self.book.id
        )
        self.assertAlmostEqual(card['average_rating'], 4.25)
        self.assertEqual(card['reviews_count'], 4)

    def test_catalog_rating_is_null_without_reviews(self):
        Book.objects.create(name='Тихая', description='.', language='ru', publishing_year=2001)
        response = self.client.get('/api/books/?search=Тихая')
        self.assertIsNone(response.json()['results'][0]['average_rating'])

    def test_filter_by_min_rating(self):
        weak = Book.objects.create(
            name='Слабая', description='.', language='ru', publishing_year=2001,
        )
        user = User.objects.create_user(username='critic', password=PASSWORD)
        Review.objects.create(user=user, book=weak, rating=2)

        response = self.client.get('/api/books/?min_rating=4')
        names = [item['name'] for item in response.json()['results']]
        self.assertIn('Имя ветра', names)
        self.assertNotIn('Слабая', names)


class SaleTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.book = Book.objects.create(
            name='Со скидкой', description='.', language='ru', publishing_year=2007,
        )
        cls.discounted = Edition.objects.create(
            book=cls.book, isbn='978-1-0000-0001-1', published_year=2020,
            price=Decimal('300.00'), old_price=Decimal('500.00'),
        )
        cls.full_price = Book.objects.create(
            name='Без скидки', description='.', language='ru', publishing_year=2008,
        )
        Edition.objects.create(
            book=cls.full_price, isbn='978-1-0000-0002-2', published_year=2020,
            price=Decimal('400.00'),
        )

    def test_discount_percent_is_computed(self):
        self.assertTrue(self.discounted.is_on_sale)
        self.assertEqual(self.discounted.discount_percent, 40)

    def test_edition_without_old_price_is_not_on_sale(self):
        edition = Edition.objects.get(book=self.full_price)
        self.assertFalse(edition.is_on_sale)
        self.assertEqual(edition.discount_percent, 0)

    def test_catalog_exposes_best_offer(self):
        response = self.client.get('/api/books/?search=скидкой')
        card = response.json()['results'][0]

        self.assertIsNotNone(card['sale'])
        self.assertEqual(card['sale']['discount_percent'], 40)
        self.assertEqual(Decimal(card['sale']['old_price']), Decimal('500.00'))

    def test_card_without_discount_has_null_sale(self):
        response = self.client.get('/api/books/?search=Без скидки')
        self.assertIsNone(response.json()['results'][0]['sale'])

    def test_on_sale_filter(self):
        response = self.client.get('/api/books/?on_sale=true')
        names = [item['name'] for item in response.json()['results']]
        self.assertEqual(names, ['Со скидкой'])

    def test_on_sale_does_not_duplicate_books_with_several_discounts(self):
        """Два издания со скидкой не должны превратить книгу в две строки выдачи."""
        Edition.objects.create(
            book=self.book, format=Edition.Format.SOFT, isbn='978-1-0000-0003-3',
            published_year=2021, price=Decimal('200.00'), old_price=Decimal('260.00'),
        )
        response = self.client.get('/api/books/?on_sale=true')
        self.assertEqual(response.json()['count'], 1)

    def test_best_offer_picks_the_deepest_discount(self):
        Edition.objects.create(
            book=self.book, format=Edition.Format.SOFT, isbn='978-1-0000-0004-4',
            published_year=2021, price=Decimal('100.00'), old_price=Decimal('400.00'),
        )
        card = self.client.get('/api/books/?search=скидкой').json()['results'][0]
        self.assertEqual(card['sale']['discount_percent'], 75)

    def test_old_price_below_price_is_rejected(self):
        staff = User.objects.create_user(username='editor', password=PASSWORD, is_staff=True)
        self.client.force_authenticate(user=staff)

        response = self.client.patch(
            '/api/editions/{}/'.format(self.discounted.id), {'old_price': '100.00'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('old_price', response.json())
