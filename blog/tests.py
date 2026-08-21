from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from blog.models import Post, Tag

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class PostVisibilityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = User.objects.create_user(
            username='editor', password=PASSWORD, is_staff=True,
        )
        cls.reader = User.objects.create_user(username='reader', password=PASSWORD)

        cls.live = Post.objects.create(
            title='Что почитать осенью', body='Текст.', author=cls.editor, is_published=True,
        )
        cls.draft = Post.objects.create(
            title='Черновик', body='Ещё не готово.', author=cls.editor, is_published=False,
        )
        cls.scheduled = Post.objects.create(
            title='Анонс на завтра',
            body='Секрет.',
            author=cls.editor,
            is_published=True,
            published_at=timezone.now() + timedelta(days=1),
        )

    def test_anonymous_sees_only_published(self):
        titles = [row['title'] for row in self.client.get('/api/blog/posts/').json()['results']]
        self.assertEqual(titles, ['Что почитать осенью'])

    def test_scheduled_post_is_hidden_until_its_date(self):
        """Отложенная публикация не должна утечь раньше срока."""
        titles = [row['title'] for row in self.client.get('/api/blog/posts/').json()['results']]
        self.assertNotIn('Анонс на завтра', titles)

        response = self.client.get('/api/blog/posts/{}/'.format(self.scheduled.slug))
        self.assertEqual(response.status_code, 404)

    def test_draft_is_hidden_from_regular_user(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/blog/posts/{}/'.format(self.draft.slug))
        self.assertEqual(response.status_code, 404)

    def test_staff_sees_drafts_and_scheduled(self):
        self.client.force_authenticate(user=self.editor)
        titles = [row['title'] for row in self.client.get('/api/blog/posts/').json()['results']]

        self.assertIn('Черновик', titles)
        self.assertIn('Анонс на завтра', titles)


class PostWriteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = User.objects.create_user(
            username='editor', password=PASSWORD, is_staff=True,
        )
        cls.reader = User.objects.create_user(username='reader', password=PASSWORD)
        cls.tag = Tag.objects.create(name='Подборки')

    def test_regular_user_cannot_publish(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.post('/api/blog/posts/', {'title': 'Моё', 'body': 'Текст.'})
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_publish(self):
        response = self.client.post('/api/blog/posts/', {'title': 'Моё', 'body': 'Текст.'})
        self.assertEqual(response.status_code, 401)

    def test_staff_can_publish_with_tags(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post('/api/blog/posts/', {
            'title': 'Десять книг про осень',
            'body': 'Текст.',
            'is_published': True,
            'tag_ids': [self.tag.id],
        })
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(title='Десять книг про осень')
        self.assertEqual(post.author, self.editor)
        self.assertEqual(list(post.tags.all()), [self.tag])

    def test_publishing_without_date_stamps_now(self):
        post = Post.objects.create(title='Сейчас', body='.', is_published=True)
        self.assertIsNotNone(post.published_at)

    def test_slug_is_generated_from_title(self):
        post = Post.objects.create(title='Что почитать осенью', body='.')
        self.assertEqual(post.slug, 'что-почитать-осенью')

    def test_duplicate_titles_get_distinct_slugs(self):
        first = Post.objects.create(title='Подборка', body='.')
        second = Post.objects.create(title='Подборка', body='.')

        self.assertNotEqual(first.slug, second.slug)
        self.assertEqual(second.slug, 'подборка-2')

    def test_editing_keeps_the_existing_slug(self):
        """Адрес опубликованного материала не должен меняться при правке текста."""
        post = Post.objects.create(title='Исходный', body='.', is_published=True)
        original = post.slug

        post.title = 'Переписанный заголовок'
        post.save()

        post.refresh_from_db()
        self.assertEqual(post.slug, original)


class PostReadTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = User.objects.create_user(
            username='editor', password=PASSWORD, is_staff=True,
        )
        cls.tag = Tag.objects.create(name='Новости')

        cls.post = Post.objects.create(
            title='Новинки месяца',
            excerpt='Коротко о главном.',
            body='Полный текст материала.',
            author=cls.editor,
            is_published=True,
        )
        cls.post.tags.add(cls.tag)

        other = Post.objects.create(title='Без тега', body='.', is_published=True)
        cls.other_slug = other.slug

    def test_list_omits_body(self):
        card = self.client.get('/api/blog/posts/').json()['results'][0]
        self.assertNotIn('body', card)
        self.assertIn('excerpt', card)

    def test_detail_returns_body_and_author(self):
        response = self.client.get('/api/blog/posts/{}/'.format(self.post.slug))
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body['body'], 'Полный текст материала.')
        self.assertEqual(body['author']['username'], 'editor')
        self.assertEqual(body['tags'][0]['name'], 'Новости')

    def test_filter_by_tag(self):
        response = self.client.get('/api/blog/posts/?tags__slug={}'.format(self.tag.slug))
        titles = [row['title'] for row in response.json()['results']]

        self.assertIn('Новинки месяца', titles)
        self.assertNotIn('Без тега', titles)

    def test_search_by_text(self):
        response = self.client.get('/api/blog/posts/?search=Новинки')
        self.assertEqual(response.json()['count'], 1)

    def test_tag_list_is_public(self):
        response = self.client.get('/api/blog/tags/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['name'], 'Новости')
