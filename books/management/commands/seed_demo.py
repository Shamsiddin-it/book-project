"""
Демо-данные для разработки: несколько книг с изданиями, героями и мудбордом.

Обложки и картинки генерируются на месте однотонными плашками в цвет книги —
так каталог выглядит осмысленно, и при этом в репозитории не нужно держать
бинарники. Команда идемпотентна: повторный запуск ничего не дублирует.

    python manage.py seed_demo
"""

import io
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from books.models import (
    Author,
    Book,
    BookAuthor,
    Category,
    Character,
    Edition,
    MoodboardImage,
)

User = get_user_model()

DEMO = [
    {
        'name': 'Имя ветра',
        'author': 'Патрик Ротфусс',
        'category': 'Фэнтези',
        'language': 'ru',
        'year': 2007,
        'accent': '#2E1F14',
        'description': (
            'История о музыканте, студенте и человеке, о котором рассказывают легенды. '
            'Он сам берётся их пересказать — с самого начала и по порядку.'
        ),
        'character': ('Квоут', 'Меня зовут Квоут. Полагаю, вы обо мне слышали.'),
        'editions': [
            ('hard', '978-5-0000-0001-1', 2020, Decimal('890.00'), 736),
            ('soft', '978-5-0000-0002-2', 2022, Decimal('540.00'), 736),
            ('ebook', '978-5-0000-0003-3', 2022, Decimal('320.00'), None),
        ],
    },
    {
        'name': 'Хоббит',
        'author': 'Джон Р. Р. Толкин',
        'category': 'Фэнтези',
        'language': 'ru',
        'year': 1937,
        'accent': '#3B5323',
        'description': (
            'Небольшой домосед против воли отправляется в путешествие через горы и леса. '
            'Ему предстоит выяснить, сколько храбрости помещается в очень тихом человеке.'
        ),
        'character': ('Бильбо Бэггинс', 'Доброе утро! — сказал Бильбо, и он именно это имел в виду.'),
        'editions': [
            ('hard', '978-5-0000-0004-4', 2019, Decimal('760.00'), 320),
            ('ebook', '978-5-0000-0005-5', 2021, Decimal('280.00'), None),
        ],
    },
    {
        'name': 'The Hobbit',
        'author': 'J. R. R. Tolkien',
        'category': 'Fantasy',
        'language': 'en',
        'year': 1937,
        'accent': '#4A5D3A',
        'description': (
            'A quiet hobbit is swept into a journey across mountains and forests, '
            'and discovers how much courage fits inside a very ordinary person.'
        ),
        'character': ('Bilbo Baggins', 'Good morning! said Bilbo, and he meant it.'),
        'editions': [
            ('soft', '978-0-0000-0006-6', 2018, Decimal('620.00'), 310),
        ],
    },
    {
        'name': 'Убийство в «Восточном экспрессе»',
        'author': 'Агата Кристи',
        'category': 'Детектив',
        'language': 'ru',
        'year': 1934,
        'accent': '#5B1A1A',
        'description': (
            'Поезд застрял в снегу, один пассажир мёртв, и все остальные что-то скрывают. '
            'К счастью, среди них едет человек с очень аккуратными усами.'
        ),
        'character': ('Эркюль Пуаро', 'Порядок и метод, мой друг. Порядок и метод.'),
        'editions': [
            ('hard', '978-5-0000-0007-7', 2021, Decimal('700.00'), 256),
            ('audio', '978-5-0000-0008-8', 2022, Decimal('450.00'), None),
        ],
    },
    {
        'name': 'Мастер и Маргарита',
        'author': 'Михаил Булгаков',
        'category': 'Классика',
        'language': 'ru',
        'year': 1967,
        'accent': '#4B2E5A',
        'description': (
            'В Москву приезжает иностранный консультант, и город перестаёт вести себя как обычно. '
            'Параллельно разворачивается совсем другая история, очень давняя.'
        ),
        'character': ('Воланд', 'Никогда и ничего не просите! Сами предложат и сами всё дадут.'),
        'editions': [
            ('hard', '978-5-0000-0009-9', 2020, Decimal('820.00'), 480),
            ('soft', '978-5-0000-0010-0', 2023, Decimal('480.00'), 480),
        ],
    },
]


def solid_image(color_hex, size=(400, 600)):
    """
    Однотонная картинка в заданный цвет.

    Pillow уже стоит как зависимость (ImageField без него не работает),
    так что дополнительных пакетов не требуется.
    """
    from PIL import Image

    color = tuple(int(color_hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='JPEG', quality=70)
    return ContentFile(buffer.getvalue())


def shade(color_hex, factor):
    """Осветляет или затемняет цвет — чтобы мудборд не был шестью одинаковыми плашками."""
    channels = [int(color_hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    adjusted = [max(0, min(255, int(value * factor))) for value in channels]
    return '#{:02x}{:02x}{:02x}'.format(*adjusted)


class Command(BaseCommand):
    help = 'Наполняет базу демонстрационными книгами для разработки.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-user',
            action='store_true',
            help='Создать тестового пользователя demo / demo-pass-12345.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created_books = 0

        for entry in DEMO:
            category, _ = Category.objects.get_or_create(name=entry['category'])
            author, _ = Author.objects.get_or_create(name=entry['author'])

            book, book_created = Book.objects.get_or_create(
                name=entry['name'],
                language=entry['language'],
                defaults={
                    'description': entry['description'],
                    'publishing_year': entry['year'],
                    'accent_color': entry['accent'],
                },
            )
            if not book_created:
                self.stdout.write(f'  пропускаю (уже есть): {book.name}')
                continue

            created_books += 1
            book.categories.add(category)
            BookAuthor.objects.get_or_create(book=book, author=author)

            for fmt, isbn, year, price, pages in entry['editions']:
                edition = Edition.objects.create(
                    book=book,
                    format=fmt,
                    isbn=isbn,
                    published_year=year,
                    price=price,
                    pages=pages,
                    publisher='Демо-издательство',
                    audio_link=(
                        'https://www.w3schools.com/html/horse.mp3' if fmt == 'audio' else None
                    ),
                )
                edition.cover.save(f'{isbn}.jpg', solid_image(entry['accent']), save=True)

                if fmt == 'ebook':
                    # Небольшой валидный PDF, чтобы ридеру было что открыть.
                    edition.file.save(
                        f'{isbn}.pdf',
                        ContentFile(
                            b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
                            b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
                            b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 400]>>endobj\n'
                            b'trailer<</Root 1 0 R>>\n%%EOF\n'
                        ),
                        save=True,
                    )

            name, quote = entry['character']
            Character.objects.create(
                book=book, name=name, signature_quote=quote, is_main=True,
            )

            for index in range(6):
                image = MoodboardImage(book=book, position=index)
                image.image.save(
                    f'{book.pk}-{index}.jpg',
                    solid_image(shade(entry['accent'], 0.7 + index * 0.18), size=(400, 400)),
                    save=False,
                )
                image.save()

            self.stdout.write(self.style.SUCCESS(f'  + {book.name}'))

        if options['with_user'] and not User.objects.filter(username='demo').exists():
            User.objects.create_user(
                username='demo', email='demo@example.com', password='demo-pass-12345',
            )
            self.stdout.write(self.style.SUCCESS('  + пользователь demo / demo-pass-12345'))

        self.stdout.write(
            self.style.SUCCESS(f'Готово. Добавлено книг: {created_books}.')
        )
