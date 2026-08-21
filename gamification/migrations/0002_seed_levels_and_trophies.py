"""
Начальные ступени и награды.

Идут миграцией, а не отдельной командой: без них эндпоинты отдают пустой
уровень и пустой список достижений, то есть раздел не работает сразу после
установки. Пороги и тексты потом правятся из админки.
"""

from django.db import migrations

LEVELS = [
    (1, 'Новичок', 0, '🌱'),
    (2, 'Читатель', 50, '📖'),
    (3, 'Книголюб', 150, '📚'),
    (4, 'Знаток', 350, '🔎'),
    (5, 'Библиофил', 700, '🏛️'),
    (6, 'Легенда полки', 1500, '👑'),
]

TROPHIES = [
    # code, name, description, icon, metric, threshold, points
    ('first-book', 'Первая книга', 'Дочитать первую книгу до конца.', '🎉', 'books_read', 1, 10),
    ('five-books', 'Пять на полке', 'Дочитать пять книг.', '📗', 'books_read', 5, 25),
    ('twenty-books', 'Двадцать книг', 'Дочитать двадцать книг.', '📚', 'books_read', 20, 100),
    ('fifty-books', 'Полсотни', 'Дочитать пятьдесят книг.', '🏆', 'books_read', 50, 250),

    ('first-review', 'Первое мнение', 'Написать первый отзыв.', '✍️', 'reviews_written', 1, 5),
    ('ten-reviews', 'Рецензент', 'Написать десять отзывов.', '🖋️', 'reviews_written', 10, 40),

    ('first-note', 'Первая заметка', 'Сохранить первую заметку или цитату.', '📝', 'notes_written', 1, 5),
    ('fifty-notes', 'Собиратель цитат', 'Сохранить пятьдесят заметок.', '🗂️', 'notes_written', 50, 60),

    ('three-genres', 'Всеядный', 'Прочитать книги из трёх разных жанров.', '🎭', 'genres_explored', 3, 20),
    ('seven-genres', 'Без границ жанра', 'Прочитать книги из семи жанров.', '🌈', 'genres_explored', 7, 60),

    ('two-languages', 'Двуязычный', 'Прочитать книги на двух языках.', '🌍', 'languages_read', 2, 30),
    ('three-languages', 'Полиглот', 'Прочитать книги на трёх языках.', '🗺️', 'languages_read', 3, 80),
]


def seed(apps, schema_editor):
    Level = apps.get_model('gamification', 'Level')
    Trophy = apps.get_model('gamification', 'Trophy')

    for number, name, min_points, icon in LEVELS:
        Level.objects.update_or_create(
            number=number,
            defaults={'name': name, 'min_points': min_points, 'icon': icon},
        )

    for code, name, description, icon, metric, threshold, points in TROPHIES:
        Trophy.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'icon': icon,
                'metric': metric,
                'threshold': threshold,
                'points': points,
            },
        )


def unseed(apps, schema_editor):
    Level = apps.get_model('gamification', 'Level')
    Trophy = apps.get_model('gamification', 'Trophy')

    Trophy.objects.filter(code__in=[row[0] for row in TROPHIES]).delete()
    Level.objects.filter(number__in=[row[0] for row in LEVELS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('gamification', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
