from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

from books.models import Book, Category, Edition
from gamification.models import Level, Metric, Trophy, UserTrophy
from gamification.services import collect_metrics, resolve_level
from notes.models import Note
from reviews.models import Review
from shelf.models import ShelfItem

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


def make_book(name, language='ru', category=None):
    book = Book.objects.create(
        name=name, description='.', language=language, publishing_year=2010,
    )
    if category:
        book.categories.add(category)
    return book


def make_edition(book, isbn):
    return Edition.objects.create(
        book=book, isbn=isbn, published_year=2015, price=Decimal('100.00'),
    )


def mark_read(user, edition):
    return ShelfItem.objects.create(
        user=user, edition=edition, status=ShelfItem.Status.READ, is_owned=True,
    )


class MetricTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='reader', password=PASSWORD)
        cls.fantasy = Category.objects.create(name='Фэнтези')
        cls.detective = Category.objects.create(name='Детектив')

    def test_only_finished_books_count(self):
        book = make_book('Читаю', category=self.fantasy)
        edition = make_edition(book, 'isbn-1')
        ShelfItem.objects.create(
            user=self.user, edition=edition, status=ShelfItem.Status.READING,
        )
        self.assertEqual(collect_metrics(self.user)[Metric.BOOKS_READ], 0)

    def test_two_editions_of_one_book_count_once(self):
        """Купить два издания одного романа — не значит прочитать две книги."""
        book = make_book('Имя ветра', category=self.fantasy)
        mark_read(self.user, make_edition(book, 'isbn-a'))
        mark_read(self.user, make_edition(book, 'isbn-b'))

        self.assertEqual(collect_metrics(self.user)[Metric.BOOKS_READ], 1)

    def test_genres_and_languages_are_distinct(self):
        mark_read(self.user, make_edition(make_book('Р1', 'ru', self.fantasy), 'i1'))
        mark_read(self.user, make_edition(make_book('Р2', 'ru', self.fantasy), 'i2'))
        mark_read(self.user, make_edition(make_book('E1', 'en', self.detective), 'i3'))

        metrics = collect_metrics(self.user)
        self.assertEqual(metrics[Metric.BOOKS_READ], 3)
        self.assertEqual(metrics[Metric.GENRES_EXPLORED], 2)
        self.assertEqual(metrics[Metric.LANGUAGES_READ], 2)

    def test_reviews_and_notes_are_counted(self):
        book = make_book('Книга', category=self.fantasy)
        Review.objects.create(user=self.user, book=book, rating=5)
        Note.objects.create(user=self.user, book=book, text='Заметка')
        Note.objects.create(user=self.user, book=book, text='Цитата', kind=Note.Kind.QUOTE)

        metrics = collect_metrics(self.user)
        self.assertEqual(metrics[Metric.REVIEWS_WRITTEN], 1)
        self.assertEqual(metrics[Metric.NOTES_WRITTEN], 2)


class LevelTests(APITestCase):
    def test_level_resolves_from_points(self):
        self.assertEqual(resolve_level(0)['level'].number, 1)
        self.assertEqual(resolve_level(49)['level'].number, 1)
        self.assertEqual(resolve_level(50)['level'].number, 2)
        self.assertEqual(resolve_level(10_000)['level'].number, 6)

    def test_progress_towards_next_level(self):
        # Между 50 и 150 половина — это 100 очков.
        result = resolve_level(100)
        self.assertEqual(result['level'].number, 2)
        self.assertEqual(result['next_level'].number, 3)
        self.assertEqual(result['points_to_next'], 50)
        self.assertEqual(result['progress'], 50)

    def test_top_level_shows_full_progress(self):
        """На максимальной ступени прогресс не должен застревать на 87%."""
        result = resolve_level(99_999)
        self.assertIsNone(result['next_level'])
        self.assertEqual(result['progress'], 100)
        self.assertEqual(result['points_to_next'], 0)


class TrophyTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='reader', password=PASSWORD)
        cls.fantasy = Category.objects.create(name='Фэнтези')

    def test_first_book_trophy_is_awarded(self):
        mark_read(self.user, make_edition(make_book('Первая', category=self.fantasy), 'i1'))

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/gamification/me/')

        self.assertEqual(response.status_code, 200)
        codes = [item['code'] for item in response.json()['newly_awarded']]
        self.assertIn('first-book', codes)

    def test_trophy_is_awarded_only_once(self):
        mark_read(self.user, make_edition(make_book('Первая', category=self.fantasy), 'i1'))
        self.client.force_authenticate(user=self.user)

        first = self.client.get('/api/gamification/me/').json()
        second = self.client.get('/api/gamification/me/').json()

        self.assertTrue(first['newly_awarded'])
        # Второй заход не должен выдавать то же самое повторно.
        self.assertEqual(second['newly_awarded'], [])
        self.assertEqual(
            UserTrophy.objects.filter(user=self.user, trophy__code='first-book').count(), 1,
        )

    def test_duplicate_award_blocked_at_database_level(self):
        trophy = Trophy.objects.get(code='first-book')
        UserTrophy.objects.create(user=self.user, trophy=trophy)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserTrophy.objects.create(user=self.user, trophy=trophy)

    def test_trophy_not_awarded_below_threshold(self):
        mark_read(self.user, make_edition(make_book('Одна', category=self.fantasy), 'i1'))

        self.client.force_authenticate(user=self.user)
        self.client.get('/api/gamification/me/')

        self.assertFalse(
            UserTrophy.objects.filter(user=self.user, trophy__code='five-books').exists()
        )

    def test_points_grow_with_activity(self):
        self.client.force_authenticate(user=self.user)
        before = self.client.get('/api/gamification/me/').json()['points']

        book = make_book('Книга', category=self.fantasy)
        mark_read(self.user, make_edition(book, 'i1'))

        after = self.client.get('/api/gamification/me/').json()['points']
        self.assertGreater(after, before)

    def test_catalogue_shows_progress_towards_unearned(self):
        mark_read(self.user, make_edition(make_book('Одна', category=self.fantasy), 'i1'))

        self.client.force_authenticate(user=self.user)
        catalogue = self.client.get('/api/gamification/trophies/').json()

        five = next(row for row in catalogue if row['trophy']['code'] == 'five-books')
        self.assertFalse(five['earned'])
        self.assertEqual(five['current'], 1)
        self.assertEqual(five['progress'], 20)

    def test_catalogue_is_visible_to_anonymous(self):
        response = self.client.get('/api/gamification/trophies/')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertFalse(response.json()[0]['earned'])

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get('/api/gamification/me/').status_code, 401)


class PublicProfileTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username='owner', password=PASSWORD)
        cls.stranger = User.objects.create_user(username='stranger', password=PASSWORD)
        category = Category.objects.create(name='Фэнтези')
        mark_read(cls.owner, make_edition(make_book('Книга', category=category), 'i1'))

    def test_public_profile_is_readable(self):
        response = self.client.get('/api/gamification/users/{}/'.format(self.owner.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'owner')

    def test_closed_shelf_hides_reading_stats(self):
        self.owner.is_shelf_public = False
        self.owner.save()

        self.client.force_authenticate(user=self.stranger)
        response = self.client.get('/api/gamification/users/{}/'.format(self.owner.id))
        self.assertEqual(response.status_code, 403)

    def test_owner_still_sees_own_closed_profile(self):
        self.owner.is_shelf_public = False
        self.owner.save()

        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/gamification/users/{}/'.format(self.owner.id))
        self.assertEqual(response.status_code, 200)


class LeaderboardTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Фэнтези')

        cls.heavy = User.objects.create_user(username='heavy', password=PASSWORD)
        for index in range(3):
            book = make_book('Книга {}'.format(index), category=cls.category)
            mark_read(cls.heavy, make_edition(book, 'heavy-{}'.format(index)))

        cls.light = User.objects.create_user(username='light', password=PASSWORD)
        mark_read(cls.light, make_edition(make_book('Одна', category=cls.category), 'light-1'))

        # Ничего не читал — в таблице ему не место.
        User.objects.create_user(username='idle', password=PASSWORD)

    def test_ranking_is_by_points(self):
        response = self.client.get('/api/gamification/leaderboard/')
        self.assertEqual(response.status_code, 200)

        rows = response.json()
        self.assertEqual(rows[0]['user']['username'], 'heavy')
        self.assertEqual(rows[0]['rank'], 1)
        self.assertEqual(rows[1]['user']['username'], 'light')

    def test_users_without_progress_are_excluded(self):
        names = [row['user']['username'] for row in self.client.get(
            '/api/gamification/leaderboard/'
        ).json()]
        self.assertNotIn('idle', names)

    def test_closed_profiles_are_excluded(self):
        self.heavy.is_shelf_public = False
        self.heavy.save()

        names = [row['user']['username'] for row in self.client.get(
            '/api/gamification/leaderboard/'
        ).json()]
        self.assertNotIn('heavy', names)

    def test_leaderboard_does_not_award_trophies(self):
        """Просмотр рейтинга не должен раздавать награды всем участникам."""
        UserTrophy.objects.all().delete()
        self.client.get('/api/gamification/leaderboard/')
        self.assertEqual(UserTrophy.objects.count(), 0)

    def test_query_count_does_not_grow_with_participants(self):
        self.client.get('/api/gamification/leaderboard/')  # прогрев

        with self.assertNumQueries(3):
            self.client.get('/api/gamification/leaderboard/')

        for index in range(15):
            user = User.objects.create_user(
                username='extra{}'.format(index), password=PASSWORD,
            )
            book = make_book('Доп {}'.format(index), category=self.category)
            mark_read(user, make_edition(book, 'extra-{}'.format(index)))

        with self.assertNumQueries(3):
            self.client.get('/api/gamification/leaderboard/')
