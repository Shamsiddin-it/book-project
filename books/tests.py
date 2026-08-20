from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from books.models import Author, Book, BookAuthor, Category, Character, Edition
from shelf.models import ShelfItem
from social.models import Like

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class CatalogTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username='reader', password=PASSWORD)
        cls.staff = User.objects.create_user(username='editor', password=PASSWORD, is_staff=True)

        cls.category = Category.objects.create(name='Фэнтези')
        cls.author = Author.objects.create(name='Патрик Ротфусс')
        cls.book = Book.objects.create(
            name='Имя ветра',
            description='История о музыканте и маге.',
            language='ru',
            publishing_year=2007,
            accent_color='#2E1F14',
        )
        cls.book.categories.add(cls.category)
        BookAuthor.objects.create(book=cls.book, author=cls.author)

        cls.hardcover = Edition.objects.create(
            book=cls.book, format=Edition.Format.HARD, isbn='978-1-0000-0001-1',
            published_year=2020, price=Decimal('350.00'), pages=736,
        )
        cls.paperback = Edition.objects.create(
            book=cls.book, format=Edition.Format.SOFT, isbn='978-1-0000-0002-2',
            published_year=2022, price=Decimal('210.00'), pages=736,
        )
        Character.objects.create(
            book=cls.book, name='Квоут', signature_quote='Меня зовут Квоут.', is_main=True,
        )

    # --- Несколько изданий одного произведения ---

    def test_book_can_have_several_editions(self):
        self.assertEqual(self.book.editions.count(), 2)

    def test_detail_returns_editions_moodboard_and_characters(self):
        response = self.client.get('/api/books/{}/'.format(self.book.id))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['editions']), 2)
        self.assertEqual(len(data['characters']), 1)
        self.assertEqual(data['characters'][0]['signature_quote'], 'Меня зовут Квоут.')
        self.assertEqual(data['accent_color'], '#2E1F14')
        self.assertEqual(data['language_display'], 'Русский')

    def test_list_shows_cheapest_edition_price(self):
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.json()['results'][0]['min_price']), Decimal('210.00'))

    def test_book_file_is_not_exposed_in_catalog(self):
        response = self.client.get('/api/books/{}/'.format(self.book.id))
        self.assertNotIn('file', response.json()['editions'][0])

    # --- Права ---

    def test_anonymous_can_read_catalog(self):
        self.assertEqual(self.client.get('/api/books/').status_code, 200)

    def test_customer_cannot_create_book(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post('/api/books/', {
            'name': 'Чужая книга', 'description': '...', 'publishing_year': 2020,
        })
        self.assertEqual(response.status_code, 403)

    def test_staff_can_create_book(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post('/api/books/', {
            'name': 'Страх мудреца', 'description': 'Продолжение.', 'publishing_year': 2011,
        })
        self.assertEqual(response.status_code, 201)

    # --- Лайки ---

    def test_toggle_like_switches_both_ways(self):
        self.client.force_authenticate(user=self.customer)
        url = '/api/books/{}/toggle_like/'.format(self.book.id)

        first = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()['liked'])
        self.assertEqual(first.json()['likes_count'], 1)

        second = self.client.post(url)
        self.assertFalse(second.json()['liked'])
        self.assertEqual(second.json()['likes_count'], 0)
        self.assertFalse(Like.objects.filter(user=self.customer, book=self.book).exists())

    def test_toggle_like_requires_authentication(self):
        response = self.client.post('/api/books/{}/toggle_like/'.format(self.book.id))
        self.assertEqual(response.status_code, 401)

    def test_is_liked_reflects_current_user(self):
        Like.objects.create(user=self.customer, book=self.book)

        anon = self.client.get('/api/books/').json()['results'][0]
        self.assertFalse(anon['is_liked'])

        self.client.force_authenticate(user=self.customer)
        mine = self.client.get('/api/books/').json()['results'][0]
        self.assertTrue(mine['is_liked'])

    def test_is_read_comes_from_shelf(self):
        self.client.force_authenticate(user=self.customer)
        self.assertFalse(self.client.get('/api/books/').json()['results'][0]['is_read'])

        ShelfItem.objects.create(
            user=self.customer, edition=self.paperback, status=ShelfItem.Status.READ,
        )
        self.assertTrue(self.client.get('/api/books/').json()['results'][0]['is_read'])

    def test_catalog_query_count_does_not_grow_with_results(self):
        """Флаги is_liked / is_read берутся двумя запросами на всю страницу, а не по книге."""
        self.client.force_authenticate(user=self.customer)

        self.client.get('/api/books/')  # прогреваем кеш соединения
        with self.assertNumQueries(6):
            self.client.get('/api/books/')

        for i in range(10):
            extra = Book.objects.create(
                name='Книга {}'.format(i), description='.', language='ru', publishing_year=2000,
            )
            Edition.objects.create(
                book=extra, isbn='978-9-0000-{:04d}-0'.format(i),
                published_year=2001, price=Decimal('100.00'),
            )

        with self.assertNumQueries(6):
            self.client.get('/api/books/')

    # --- Фильтры и поиск ---

    def test_filter_by_language(self):
        self.assertEqual(self.client.get('/api/books/?language=ru').json()['count'], 1)
        self.assertEqual(self.client.get('/api/books/?language=en').json()['count'], 0)

    def test_search_by_name_and_author(self):
        self.assertEqual(self.client.get('/api/books/?search=ветра').json()['count'], 1)
        self.assertEqual(self.client.get('/api/books/?search=Ротфусс').json()['count'], 1)

    def test_author_books_amount_is_computed(self):
        response = self.client.get('/api/authors/')
        self.assertEqual(response.json()['results'][0]['books_amount'], 1)


class EditionConstraintTests(APITestCase):
    def test_two_editions_can_share_a_book_but_not_an_isbn(self):
        from django.db import IntegrityError, transaction

        book = Book.objects.create(
            name='Тестовая', description='.', language='ru', publishing_year=1999,
        )
        Edition.objects.create(
            book=book, isbn='978-0-0000-0000-1', published_year=1999, price=Decimal('10.00'),
        )
        Edition.objects.create(
            book=book, isbn='978-0-0000-0000-2', published_year=2005, price=Decimal('20.00'),
        )
        self.assertEqual(book.editions.count(), 2)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Edition.objects.create(
                    book=book, isbn='978-0-0000-0000-1',
                    published_year=2010, price=Decimal('30.00'),
                )
