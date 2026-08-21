from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from books.models import Author, Book, BookAuthor, Category, Edition
from reviews.models import Review
from shelf.models import ShelfItem
from social.models import Like

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


def make_book(name, language='ru', categories=(), authors=()):
    book = Book.objects.create(
        name=name, description='.', language=language, publishing_year=2010,
    )
    if categories:
        book.categories.set(categories)
    for author in authors:
        BookAuthor.objects.create(book=book, author=author)
    Edition.objects.create(
        book=book, isbn='isbn-{}'.format(name), published_year=2015, price=Decimal('100.00'),
    )
    return book


class SimilarBooksTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fantasy = Category.objects.create(name='Фэнтези')
        cls.detective = Category.objects.create(name='Детектив')

        cls.anchor = make_book('Имя ветра', categories=[cls.fantasy])
        cls.strong = make_book('Страх мудреца', categories=[cls.fantasy])
        cls.weak = make_book('Обливион', categories=[cls.fantasy])
        cls.unrelated = make_book('Убийство в поезде', categories=[cls.detective])

        # Трое читали и «Имя ветра», и «Страх мудреца»; один — «Обливион».
        for i in range(3):
            reader = User.objects.create_user(username='fan{}'.format(i), password=PASSWORD)
            Like.objects.create(user=reader, book=cls.anchor)
            Like.objects.create(user=reader, book=cls.strong)

        loner = User.objects.create_user(username='loner', password=PASSWORD)
        Like.objects.create(user=loner, book=cls.anchor)
        Like.objects.create(user=loner, book=cls.weak)

    def test_co_read_book_ranks_first(self):
        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))
        self.assertEqual(response.status_code, 200)

        names = [item['name'] for item in response.json()['results']]
        self.assertEqual(names[0], 'Страх мудреца')
        self.assertIn('Обливион', names)

    def test_anchor_book_is_never_recommended_to_itself(self):
        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))
        names = [item['name'] for item in response.json()['results']]
        self.assertNotIn('Имя ветра', names)

    def test_available_to_anonymous(self):
        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()['count'], 0)

    def test_already_read_books_are_not_recommended(self):
        reader = User.objects.create_user(username='veteran', password=PASSWORD)
        Like.objects.create(user=reader, book=self.strong)

        self.client.force_authenticate(user=reader)
        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))

        names = [item['name'] for item in response.json()['results']]
        self.assertNotIn('Страх мудреца', names)

    def test_cold_start_falls_back_to_genre(self):
        """У книги без единого читателя всё равно должны быть соседи по жанру."""
        lonely = make_book('Никем не читанная', categories=[self.fantasy])

        response = self.client.get('/api/recommendations/similar/{}/'.format(lonely.id))
        names = [item['name'] for item in response.json()['results']]

        self.assertGreater(len(names), 0)
        self.assertIn('Имя ветра', names)

    def test_limit_is_capped(self):
        response = self.client.get(
            '/api/recommendations/similar/{}/?limit=9999'.format(self.anchor.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.json()['count'], 50)

    def test_garbage_limit_does_not_crash(self):
        response = self.client.get(
            '/api/recommendations/similar/{}/?limit=abc'.format(self.anchor.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_inactive_book_returns_404(self):
        self.anchor.is_active = False
        self.anchor.save()
        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))
        self.assertEqual(response.status_code, 404)

    def test_inactive_books_are_never_recommended(self):
        self.strong.is_active = False
        self.strong.save()

        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))
        names = [item['name'] for item in response.json()['results']]
        self.assertNotIn('Страх мудреца', names)


class PersonalRecommendationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fantasy = Category.objects.create(name='Фэнтези')
        cls.rothfuss = Author.objects.create(name='Патрик Ротфусс')

        cls.liked = make_book('Имя ветра', categories=[cls.fantasy], authors=[cls.rothfuss])
        cls.target = make_book('Страх мудреца', categories=[cls.fantasy])
        cls.english = make_book('The Hobbit', language='en', categories=[cls.fantasy])

        cls.me = User.objects.create_user(username='me', password=PASSWORD)
        Like.objects.create(user=cls.me, book=cls.liked)

        # Сосед по вкусу: читал то же, плюс кое-что ещё.
        peer = User.objects.create_user(username='peer', password=PASSWORD)
        Like.objects.create(user=peer, book=cls.liked)
        Like.objects.create(user=peer, book=cls.target)

    def test_requires_authentication(self):
        self.assertEqual(self.client.get('/api/recommendations/').status_code, 401)

    def test_collaborative_recommendation(self):
        self.client.force_authenticate(user=self.me)
        response = self.client.get('/api/recommendations/')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['basis'], 'collaborative')

        names = [item['name'] for item in body['results']]
        self.assertEqual(names[0], 'Страх мудреца')

    def test_own_taste_is_excluded(self):
        self.client.force_authenticate(user=self.me)
        names = [item['name'] for item in self.client.get('/api/recommendations/').json()['results']]
        self.assertNotIn('Имя ветра', names)

    def test_new_user_gets_popular_books(self):
        newcomer = User.objects.create_user(username='newcomer', password=PASSWORD)
        self.client.force_authenticate(user=newcomer)

        body = self.client.get('/api/recommendations/').json()
        self.assertEqual(body['basis'], 'popular')
        self.assertGreater(body['count'], 0)

    def test_shelf_counts_as_taste_but_want_to_read_does_not(self):
        quiet = User.objects.create_user(username='quiet', password=PASSWORD)
        edition = self.liked.editions.first()

        # «Хочу прочитать» — ещё не сигнал о вкусе.
        item = ShelfItem.objects.create(
            user=quiet, edition=edition, status=ShelfItem.Status.WANT_TO_READ,
        )
        self.client.force_authenticate(user=quiet)
        self.assertEqual(self.client.get('/api/recommendations/').json()['basis'], 'popular')

        # А «прочитано» — уже сигнал.
        item.status = ShelfItem.Status.READ
        item.save()
        self.assertNotEqual(self.client.get('/api/recommendations/').json()['basis'], 'popular')

    def test_language_filter(self):
        self.client.force_authenticate(user=self.me)
        response = self.client.get('/api/recommendations/?language=en')

        names = [item['name'] for item in response.json()['results']]
        self.assertIn('The Hobbit', names)
        self.assertNotIn('Страх мудреца', names)

    def test_taste_fallback_when_nobody_overlaps(self):
        """Совпадений по людям нет — рекомендуем по жанру, который человек уже выбирал."""
        solo = User.objects.create_user(username='solo', password=PASSWORD)
        obscure = make_book('Одинокая книга', categories=[self.fantasy])
        Like.objects.create(user=solo, book=obscure)

        self.client.force_authenticate(user=solo)
        body = self.client.get('/api/recommendations/').json()

        self.assertIn(body['basis'], {'taste', 'mixed'})
        names = [item['name'] for item in body['results']]
        self.assertNotIn('Одинокая книга', names)
        self.assertGreater(len(names), 0)

    def test_query_count_stays_bounded_as_catalogue_grows(self):
        """
        Алгоритм работает множествами id, а не обходом книг по одной.
        Точное число запросов зависит от того, сколько ступеней запасного пути
        понадобилось, поэтому проверяем не равенство, а что счётчик остаётся
        ограниченным и не растёт вместе с каталогом.
        """
        self.client.force_authenticate(user=self.me)

        for i in range(5):
            make_book('Наполнитель {}'.format(i), categories=[self.fantasy])
        self.client.get('/api/recommendations/')  # прогрев

        with CaptureQueriesContext(connection) as small:
            self.client.get('/api/recommendations/')

        for i in range(40):
            make_book('Ещё наполнитель {}'.format(i), categories=[self.fantasy])

        with CaptureQueriesContext(connection) as large:
            self.client.get('/api/recommendations/')

        self.assertLessEqual(len(small), 20)
        self.assertLessEqual(len(large), 20)
        # Каталог вырос в девять раз — запросов больше стать не должно.
        self.assertLessEqual(len(large), len(small))


class LanguageListTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        make_book('Имя ветра', language='ru')
        make_book('Другая русская', language='ru')
        make_book('The Hobbit', language='en')

    def test_lists_only_languages_that_have_books(self):
        response = self.client.get('/api/languages/')
        self.assertEqual(response.status_code, 200)

        by_code = {row['code']: row for row in response.json()}
        self.assertEqual(by_code['ru']['books_count'], 2)
        self.assertEqual(by_code['en']['books_count'], 1)
        self.assertNotIn('fr', by_code)

    def test_available_to_anonymous(self):
        self.assertEqual(self.client.get('/api/languages/').status_code, 200)

    def test_inactive_books_are_not_counted(self):
        Book.objects.filter(language='en').update(is_active=False)
        by_code = {row['code']: row for row in self.client.get('/api/languages/').json()}
        self.assertNotIn('en', by_code)

class SerializerContractTests(APITestCase):
    """
    Рекомендации отдают книги тем же сериализатором, что и каталог.
    Если выборку забыть аннотировать, поля рейтинга молча исчезают из ответа,
    и фронт получает undefined там, где по контракту число. Так уже было.
    """

    @classmethod
    def setUpTestData(cls):
        cls.fantasy = Category.objects.create(name='Фэнтези')
        cls.anchor = make_book('Имя ветра', categories=[cls.fantasy])
        cls.other = make_book('Страх мудреца', categories=[cls.fantasy])

        cls.reader = User.objects.create_user(username='reader', password=PASSWORD)
        Like.objects.create(user=cls.reader, book=cls.anchor)

    REQUIRED_FIELDS = {
        'id', 'name', 'language', 'language_display', 'authors', 'accent_color',
        'cover', 'min_price', 'sale', 'average_rating', 'reviews_count',
        'is_liked', 'is_read',
    }

    def test_similar_books_carry_every_card_field(self):
        response = self.client.get('/api/recommendations/similar/{}/'.format(self.anchor.id))
        self.assertEqual(response.status_code, 200)

        results = response.json()['results']
        self.assertGreater(len(results), 0)
        for item in results:
            self.assertEqual(self.REQUIRED_FIELDS - set(item), set())

    def test_personal_recommendations_carry_every_card_field(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/recommendations/')

        results = response.json()['results']
        self.assertGreater(len(results), 0)
        for item in results:
            self.assertEqual(self.REQUIRED_FIELDS - set(item), set())

    def test_rating_matches_the_catalogue(self):
        User.objects.create_user(username='critic', password=PASSWORD)
        Review.objects.create(
            user=User.objects.get(username='critic'), book=self.other, rating=4,
        )

        similar = self.client.get(
            '/api/recommendations/similar/{}/'.format(self.anchor.id)
        ).json()['results']
        card = next(item for item in similar if item['id'] == self.other.id)

        self.assertEqual(card['average_rating'], 4.0)
        self.assertEqual(card['reviews_count'], 1)
