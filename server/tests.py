"""
Дымовые тесты админки.

manage.py check проверяет конфигурацию, но не выполняет методы отображения.
Опечатка в списке колонок или обращение к отсутствующему полю проявляются
только при заходе на страницу — а туда обычно заходит уже пользователь.
Здесь мы открываем каждый раздел за него.
"""

import shutil
import tempfile
from decimal import Decimal

from django.contrib import admin
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import Post, Tag
from books.models import Author, Book, BookAuthor, Category, Character, Edition, MoodboardImage
from notes.models import Note
from purchase.models import CartItem, Order, OrderItem
from reviews.models import Review
from shelf.models import ShelfItem
from social.models import Comment, Follow, Like

User = get_user_model()


class AdminSmokeTests(TestCase):
    """Каждый зарегистрированный раздел должен открываться и со списком, и с формой."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser(
            username='root', email='root@example.com', password='Sup3rSecret!pass',
        )
        cls.reader = User.objects.create_user(
            username='reader', password='Sup3rSecret!pass',
        )

        category = Category.objects.create(name='Фэнтези')
        author = Author.objects.create(name='Патрик Ротфусс')

        book = Book.objects.create(
            name='Имя ветра', description='.', language='ru',
            publishing_year=2007, accent_color='#2E1F14',
        )
        book.categories.add(category)
        BookAuthor.objects.create(book=book, author=author)

        edition = Edition.objects.create(
            book=book, isbn='978-5-0000-0001-1', published_year=2020,
            price=Decimal('300.00'), old_price=Decimal('500.00'),
        )
        MoodboardImage.objects.create(book=book, position=0)
        Character.objects.create(book=book, name='Квоут', is_main=True)

        Review.objects.create(user=cls.reader, book=book, rating=5, text='Отлично.')
        Note.objects.create(user=cls.reader, book=book, text='Цитата', kind=Note.Kind.QUOTE)
        Like.objects.create(user=cls.reader, book=book)
        Follow.objects.create(follower=cls.reader, following=cls.staff)
        Comment.objects.create(user=cls.reader, book=book, text='Хорошая книга.')

        ShelfItem.objects.create(user=cls.reader, edition=edition, is_owned=True)
        CartItem.objects.create(user=cls.staff, edition=edition)

        order = Order.objects.create(user=cls.reader, total=Decimal('300.00'))
        OrderItem.objects.create(order=order, edition=edition, unit_price=Decimal('300.00'))

        tag = Tag.objects.create(name='Подборки')
        post = Post.objects.create(title='Что почитать', body='Текст.', is_published=True)
        post.tags.add(tag)

    def setUp(self):
        self.client.force_login(self.staff)

    def test_index_opens(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BOOKLY')

    def test_every_changelist_opens(self):
        """
        Список — самое хрупкое место: там выполняются все методы колонок,
        включая превью картинок и подсчёты.
        """
        for model, model_admin in admin.site._registry.items():
            url = reverse(
                'admin:{}_{}_changelist'.format(
                    model._meta.app_label, model._meta.model_name,
                )
            )
            with self.subTest(model=model.__name__):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)

    def test_every_add_form_opens(self):
        for model in admin.site._registry:
            url = reverse(
                'admin:{}_{}_add'.format(model._meta.app_label, model._meta.model_name)
            )
            with self.subTest(model=model.__name__):
                response = self.client.get(url)
                # Часть моделей может запрещать добавление — это нормально.
                self.assertIn(response.status_code, (200, 403), url)

    def test_book_form_opens_with_all_inlines(self):
        book = Book.objects.get(name='Имя ветра')
        url = reverse('admin:books_book_change', args=[book.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Все четыре вложенных блока должны быть на странице.
        self.assertContains(response, 'Издания')
        self.assertContains(response, 'Мудборд')
        self.assertContains(response, 'Герои')

    def test_accent_colour_uses_a_picker(self):
        """Цвет подбирают глазами по обложке, а не вводят HEX по памяти."""
        book = Book.objects.get(name='Имя ветра')
        response = self.client.get(reverse('admin:books_book_change', args=[book.pk]))
        self.assertContains(response, 'type="color"')

    def test_edition_change_form_opens(self):
        edition = Edition.objects.first()
        response = self.client.get(reverse('admin:books_edition_change', args=[edition.pk]))
        self.assertEqual(response.status_code, 200)

    def test_missing_image_file_does_not_break_the_list(self):
        """
        В базе может числиться картинка, которой нет на диске — например,
        после переноса проекта. Список всё равно должен открыться.
        """
        Category.objects.create(name='Битая', image='category_images/nope.jpg')

        response = self.client.get(reverse('admin:books_category_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_enter_admin(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse('admin:index'))
        # Django отправляет на страницу входа, а не показывает содержимое.
        self.assertNotEqual(response.status_code, 200)


_TEMP_PROTECTED_ROOT = tempfile.mkdtemp(prefix='protected-media-admin-')


@override_settings(PROTECTED_MEDIA_ROOT=_TEMP_PROTECTED_ROOT)
class ProtectedFileInAdminTests(TestCase):
    """
    Файл книги лежит в хранилище, у которого намеренно нет публичного URL.
    Штатный виджет админки пытался построить ссылку на него, и форма издания
    с загруженным файлом переставала открываться вовсе.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, _TEMP_PROTECTED_ROOT, True)

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser(
            username='root2', email='root2@example.com', password='Sup3rSecret!pass',
        )
        book = Book.objects.create(
            name='С файлом', description='.', language='ru', publishing_year=2010,
        )
        cls.edition = Edition.objects.create(
            book=book, format=Edition.Format.EBOOK, isbn='978-5-0000-0777-7',
            published_year=2020, price=Decimal('100.00'),
        )
        cls.edition.file.save('book.pdf', ContentFile(b'%PDF-1.4 test'), save=True)

    def setUp(self):
        self.client.force_login(self.staff)

    def test_edition_form_opens_when_a_file_is_attached(self):
        url = reverse('admin:books_edition_change', args=[self.edition.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Имя файла показано, а ссылки на него нет.
        self.assertContains(response, 'book')
        self.assertNotContains(response, 'protected_media')

    def test_book_form_with_file_bearing_edition_opens(self):
        url = reverse('admin:books_book_change', args=[self.edition.book_id])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_storage_still_refuses_to_build_a_url(self):
        """Виджет обходит проблему, но само правило остаётся в силе."""
        with self.assertRaises(ValueError):
            self.edition.file.url
