import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from books.models import Book, Edition
from shelf.models import ShelfItem

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'
BOOK_BYTES = b'%PDF-1.4 fake book content for tests'

_TEMP_PROTECTED_ROOT = tempfile.mkdtemp(prefix='protected-media-test-')


@override_settings(PROTECTED_MEDIA_ROOT=_TEMP_PROTECTED_ROOT)
class ReaderTestCase(APITestCase):
    """Общая обвязка: издание с файлом, владелец и посторонний."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, _TEMP_PROTECTED_ROOT, True)

    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(username='owner', password=PASSWORD)
        self.stranger = User.objects.create_user(username='stranger', password=PASSWORD)

        self.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru',
            publishing_year=2007, accent_color='#2E1F14',
        )
        self.edition = Edition.objects.create(
            book=self.book, format=Edition.Format.EBOOK, isbn='978-1-0000-0001-1',
            published_year=2020, price=Decimal('350.00'),
            file=SimpleUploadedFile('name-of-the-wind.pdf', BOOK_BYTES),
        )
        self.owned = ShelfItem.objects.create(
            user=self.owner, edition=self.edition, is_owned=True,
        )

    def manifest_url(self):
        return '/api/reader/{}/'.format(self.edition.id)

    def content_url(self):
        return '/api/reader/{}/content/'.format(self.edition.id)

    def progress_url(self):
        return '/api/reader/{}/progress/'.format(self.edition.id)


class ReaderAccessTests(ReaderTestCase):
    def test_owner_can_read_content(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.content_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), BOOK_BYTES)

    def test_anonymous_cannot_read_content(self):
        self.assertEqual(self.client.get(self.content_url()).status_code, 401)
        self.assertEqual(self.client.get(self.manifest_url()).status_code, 401)

    def test_stranger_cannot_read_content(self):
        self.client.force_authenticate(user=self.stranger)
        self.assertEqual(self.client.get(self.content_url()).status_code, 403)
        self.assertEqual(self.client.get(self.manifest_url()).status_code, 403)

    def test_shelf_item_without_purchase_is_not_enough(self):
        """Книга на полке со статусом «хочу прочитать» — ещё не купленная книга."""
        ShelfItem.objects.create(user=self.stranger, edition=self.edition, is_owned=False)

        self.client.force_authenticate(user=self.stranger)
        self.assertEqual(self.client.get(self.content_url()).status_code, 403)

    def test_revoking_ownership_revokes_access(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get(self.content_url()).status_code, 200)

        self.owned.is_owned = False
        self.owned.save()

        self.assertEqual(self.client.get(self.content_url()).status_code, 403)

    def test_staff_can_read_for_moderation(self):
        moderator = User.objects.create_user(username='mod', password=PASSWORD, is_staff=True)
        self.client.force_authenticate(user=moderator)
        self.assertEqual(self.client.get(self.content_url()).status_code, 200)

    def test_inactive_edition_is_not_served(self):
        self.edition.is_active = False
        self.edition.save()

        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get(self.content_url()).status_code, 404)

    def test_file_has_no_public_url(self):
        """
        Приватное хранилище не должно уметь строить публичную ссылку —
        иначе файл утёк бы мимо всех проверок.
        """
        with self.assertRaises(ValueError):
            self.edition.file.url

    def test_content_is_not_cacheable_by_proxies(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.content_url())
        self.assertIn('no-store', response['Cache-Control'])

    @override_settings(
        PROTECTED_MEDIA_ACCEL_HEADER='X-Accel-Redirect',
        PROTECTED_MEDIA_INTERNAL_URL='/protected/',
    )
    def test_accel_header_delegates_to_web_server(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.content_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertTrue(response['X-Accel-Redirect'].startswith('/protected/book_files/'))


class ReaderManifestTests(ReaderTestCase):
    def test_manifest_describes_the_edition(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.manifest_url())

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['book_name'], 'Имя ветра')
        self.assertEqual(data['accent_color'], '#2E1F14')
        self.assertEqual(data['format'], 'ebook')
        self.assertFalse(data['is_audio'])
        self.assertEqual(data['size_bytes'], len(BOOK_BYTES))
        self.assertTrue(data['content_url'].endswith('/content/'))

    def test_manifest_returns_saved_position(self):
        self.owned.progress_percent = 37
        self.owned.position = 'epubcfi(/6/14!/4/2/14/2:0)'
        self.owned.save()

        self.client.force_authenticate(user=self.owner)
        data = self.client.get(self.manifest_url()).json()

        self.assertEqual(data['progress_percent'], 37)
        self.assertEqual(data['position'], 'epubcfi(/6/14!/4/2/14/2:0)')

    def test_audio_edition_is_flagged(self):
        audio = Edition.objects.create(
            book=self.book, format=Edition.Format.AUDIO, isbn='978-1-0000-0009-9',
            published_year=2021, price=Decimal('200.00'),
            audio_link='https://example.com/audio.m3u8',
        )
        ShelfItem.objects.create(user=self.owner, edition=audio, is_owned=True)

        self.client.force_authenticate(user=self.owner)
        data = self.client.get('/api/reader/{}/'.format(audio.id)).json()

        self.assertTrue(data['is_audio'])
        self.assertEqual(data['audio_link'], 'https://example.com/audio.m3u8')
        self.assertIsNone(data['content_url'])

    def test_audio_link_hidden_from_non_owner(self):
        self.client.force_authenticate(user=self.stranger)
        self.assertEqual(self.client.get(self.manifest_url()).status_code, 403)


class ReadingProgressTests(ReaderTestCase):
    def test_saving_progress_moves_status_to_reading(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.progress_url(), {
            'progress_percent': 15, 'position': 'page-42',
        })

        self.assertEqual(response.status_code, 200)
        self.owned.refresh_from_db()
        self.assertEqual(self.owned.progress_percent, 15)
        self.assertEqual(self.owned.position, 'page-42')
        self.assertEqual(self.owned.status, ShelfItem.Status.READING)
        self.assertIsNotNone(self.owned.last_read_at)

    def test_finishing_the_book_completes_the_shelf_item(self):
        self.client.force_authenticate(user=self.owner)
        self.client.patch(self.progress_url(), {'progress_percent': 100})

        self.owned.refresh_from_db()
        self.assertEqual(self.owned.status, ShelfItem.Status.READ)
        self.assertIsNotNone(self.owned.finished_at)

    def test_progress_out_of_range_is_rejected(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.patch(self.progress_url(), {'progress_percent': 101}).status_code, 400,
        )

    def test_status_cannot_be_forced_through_progress_endpoint(self):
        self.client.force_authenticate(user=self.owner)
        self.client.patch(self.progress_url(), {'progress_percent': 5, 'status': 'read'})

        self.owned.refresh_from_db()
        self.assertEqual(self.owned.status, ShelfItem.Status.READING)

    def test_stranger_cannot_read_or_write_progress(self):
        self.client.force_authenticate(user=self.stranger)
        self.assertEqual(self.client.get(self.progress_url()).status_code, 403)
        self.assertEqual(
            self.client.patch(self.progress_url(), {'progress_percent': 50}).status_code, 403,
        )

    def test_progress_is_per_user(self):
        second_owner = User.objects.create_user(username='second', password=PASSWORD)
        other_item = ShelfItem.objects.create(
            user=second_owner, edition=self.edition, is_owned=True,
        )

        self.client.force_authenticate(user=self.owner)
        self.client.patch(self.progress_url(), {'progress_percent': 80})

        other_item.refresh_from_db()
        self.assertEqual(other_item.progress_percent, 0)

    def test_shelf_shows_position_saved_by_reader(self):
        self.client.force_authenticate(user=self.owner)
        self.client.patch(self.progress_url(), {'progress_percent': 20, 'position': 'page-7'})

        shelf = self.client.get('/api/shelf/').json()['results'][0]
        self.assertEqual(shelf['position'], 'page-7')
        self.assertEqual(shelf['progress_percent'], 20)

    def test_position_cannot_be_written_through_shelf_endpoint(self):
        """Место чтения пишет только ридер, иначе два источника правды."""
        self.client.force_authenticate(user=self.owner)
        self.client.patch('/api/shelf/{}/'.format(self.owned.id), {'position': 'hacked'})

        self.owned.refresh_from_db()
        self.assertEqual(self.owned.position, '')
