"""
Общие детали для админки: превью картинок и удобные поля ввода.

Всё держится здесь, а не расползается по приложениям, потому что обложки,
аватары и мудборды показываются одинаково в семи местах.
"""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html


def thumbnail(image_field, height=60, radius=6):
    """
    Картинка-превью для списка или формы.

    Файл может числиться в базе, но отсутствовать на диске — например, после
    переноса проекта. Тогда обращение к .url бросает исключение и роняет
    всю страницу списка, поэтому оно перехвачено.
    """
    if not image_field:
        return format_html('<span style="color:#999">—</span>')

    try:
        url = image_field.url
    except (ValueError, OSError):
        return format_html('<span style="color:#c00">файл потерян</span>')

    return format_html(
        '<img src="{}" style="height:{}px;width:auto;border-radius:{}px;'
        'object-fit:cover;border:1px solid #ddd" loading="lazy" />',
        url,
        height,
        radius,
    )


def preview_field(attribute, label, height=60):
    """
    Собирает метод-превью для admin-класса.

    Позволяет не писать один и тот же трёхстрочный метод в каждом ModelAdmin.
    """

    @admin.display(description=label)
    def render(self, obj):
        return thumbnail(getattr(obj, attribute, None), height=height)

    return render


class ColorInput(forms.TextInput):
    """
    Нативный выбор цвета вместо ручного ввода HEX.

    Рядом остаётся текстовое поле: браузерный выбор не даёт скопировать
    значение и не показывает сам код, а он нужен, когда цвет подбирают
    под конкретную обложку.
    """

    input_type = 'color'

    def render(self, name, value, attrs=None, renderer=None):
        picker = super().render(name, value, attrs, renderer)
        return format_html(
            '<div style="display:flex;gap:8px;align-items:center">'
            '{}<code style="color:#666">{}</code></div>',
            picker,
            value or 'не задан',
        )


class ImagePreviewMixin:
    """
    Показывает текущую картинку прямо в форме редактирования.

    Без этого при загрузке новой обложки не видно старую — приходится
    открывать файл в соседней вкладке, чтобы понять, что там сейчас.
    """

    preview_source = 'image'

    @admin.display(description='Текущее изображение')
    def current_image(self, obj):
        if obj is None or not obj.pk:
            return format_html('<span style="color:#999">Появится после сохранения</span>')
        return thumbnail(getattr(obj, self.preview_source, None), height=180)


class ProtectedFileWidget(AdminFileWidget):
    """
    Поле файла для книг, лежащих в закрытом хранилище.

    Штатный виджет админки рисует ссылку «Текущий файл» и для этого зовёт
    file.url. У ProtectedStorage такого URL нет — он намеренно бросает
    исключение, — и форма издания с загруженным файлом просто не открывалась.

    Здесь вместо ссылки показывается имя файла: открыть его всё равно можно
    только через ридер, после проверки покупки.
    """

    def render(self, name, value, attrs=None, renderer=None):
        # Виджет получает FieldFile; подсовываем в родителя пустое значение,
        # чтобы он не пытался построить ссылку, а имя файла выводим сами.
        uploader = super().render(name, None, attrs, renderer)

        if not value:
            return format_html(
                '<div>{}<p class="help">Файл не загружен.</p></div>', uploader,
            )

        return format_html(
            '<div><p><strong>Загружен:</strong> <code>{}</code></p>'
            '<p class="help">Прямой ссылки на файл нет — он отдаётся только '
            'владельцу издания через ридер. Чтобы заменить, выберите новый файл.</p>'
            '{}</div>',
            value.name,
            uploader,
        )
