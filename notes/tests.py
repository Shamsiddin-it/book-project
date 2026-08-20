from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from books.models import Book
from notes.models import Note

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class NoteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)
        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )

    def test_create_note_and_quote(self):
        self.client.force_authenticate(user=self.alice)

        note = self.client.post('/api/notes/', {
            'book': self.book.id, 'text': 'Перечитать вторую главу.', 'page': 42,
        })
        self.assertEqual(note.status_code, 201)
        self.assertEqual(note.json()['kind'], 'note')
        self.assertEqual(note.json()['user']['username'], 'alice')

        quote = self.client.post('/api/notes/', {
            'book': self.book.id, 'kind': 'quote', 'text': 'Меня зовут Квоут.',
        })
        self.assertEqual(quote.status_code, 201)
        self.assertEqual(quote.json()['kind_display'], 'Цитата')

    def test_notes_require_authentication(self):
        self.assertEqual(self.client.get('/api/notes/').status_code, 401)

    def test_blank_text_is_rejected(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/notes/', {'book': self.book.id, 'text': '   '})
        self.assertEqual(response.status_code, 400)

    def test_list_shows_only_own_notes(self):
        Note.objects.create(user=self.alice, book=self.book, text='Моя')
        Note.objects.create(user=self.bob, book=self.book, text='Чужая')

        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/notes/')
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['text'], 'Моя')

    def test_cannot_reach_someone_elses_note_by_id(self):
        note = Note.objects.create(user=self.bob, book=self.book, text='Личное')
        self.client.force_authenticate(user=self.alice)

        self.assertEqual(self.client.get('/api/notes/{}/'.format(note.id)).status_code, 404)
        self.assertEqual(self.client.delete('/api/notes/{}/'.format(note.id)).status_code, 404)
        self.assertTrue(Note.objects.filter(pk=note.pk).exists())

    def test_filter_by_kind_and_book(self):
        Note.objects.create(user=self.alice, book=self.book, text='Заметка', kind=Note.Kind.NOTE)
        Note.objects.create(user=self.alice, book=self.book, text='Цитата', kind=Note.Kind.QUOTE)

        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get('/api/notes/?kind=quote').json()['count'], 1)
        self.assertEqual(
            self.client.get('/api/notes/?book={}'.format(self.book.id)).json()['count'], 2,
        )


class PublicNoteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)
        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )
        cls.public = Note.objects.create(
            user=cls.alice, book=cls.book, text='Публичная цитата',
            kind=Note.Kind.QUOTE, is_public=True,
        )
        cls.private = Note.objects.create(
            user=cls.alice, book=cls.book, text='Личное', is_public=False,
        )

    def test_private_notes_are_never_exposed_to_others(self):
        response = self.client.get('/api/notes/users/{}/'.format(self.alice.id))
        self.assertEqual(response.status_code, 200)

        texts = [n['text'] for n in response.json()['results']]
        self.assertIn('Публичная цитата', texts)
        self.assertNotIn('Личное', texts)

    def test_owner_sees_own_private_notes(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/notes/users/{}/'.format(self.alice.id))
        self.assertEqual(response.json()['count'], 2)

    def test_closed_shelf_hides_notes(self):
        self.alice.is_shelf_public = False
        self.alice.save()

        self.client.force_authenticate(user=self.bob)
        response = self.client.get('/api/notes/users/{}/'.format(self.alice.id))
        self.assertEqual(response.status_code, 403)

    def test_book_notes_show_public_only(self):
        response = self.client.get('/api/notes/books/{}/'.format(self.book.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['text'], 'Публичная цитата')

    def test_book_notes_respect_closed_shelf(self):
        self.alice.is_shelf_public = False
        self.alice.save()

        response = self.client.get('/api/notes/books/{}/'.format(self.book.id))
        self.assertEqual(response.json()['count'], 0)

    def test_book_notes_can_filter_quotes(self):
        Note.objects.create(
            user=self.bob, book=self.book, text='Обычная заметка', kind=Note.Kind.NOTE,
        )
        response = self.client.get('/api/notes/books/{}/?kind=quote'.format(self.book.id))
        self.assertEqual(response.json()['count'], 1)
