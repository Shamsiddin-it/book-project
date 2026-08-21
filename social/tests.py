from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

from books.models import Book, Character
from social.models import Comment, CommentLike, Follow

User = get_user_model()

PASSWORD = 'Sup3rSecret!pass'


class FollowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)

    def test_toggle_follow_both_ways(self):
        self.client.force_authenticate(user=self.alice)
        url = '/api/social/users/{}/follow/'.format(self.bob.id)

        first = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()['following'])
        self.assertEqual(first.json()['followers_count'], 1)

        second = self.client.post(url)
        self.assertFalse(second.json()['following'])
        self.assertEqual(second.json()['followers_count'], 0)

    def test_cannot_follow_self(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/social/users/{}/follow/'.format(self.alice.id))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Follow.objects.exists())

    def test_self_follow_blocked_at_database_level(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.alice, following=self.alice)

    def test_follow_requires_authentication(self):
        response = self.client.post('/api/social/users/{}/follow/'.format(self.bob.id))
        self.assertEqual(response.status_code, 401)

    def test_followers_and_following_lists(self):
        Follow.objects.create(follower=self.alice, following=self.bob)

        followers = self.client.get('/api/social/users/{}/followers/'.format(self.bob.id))
        self.assertEqual(followers.status_code, 200)
        self.assertEqual([u['username'] for u in followers.json()['results']], ['alice'])

        following = self.client.get('/api/social/users/{}/following/'.format(self.alice.id))
        self.assertEqual([u['username'] for u in following.json()['results']], ['bob'])

        # И обратные направления пусты.
        self.assertEqual(
            self.client.get('/api/social/users/{}/followers/'.format(self.alice.id)).json()['count'], 0
        )

    def test_counts_are_exposed_on_public_profile(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        response = self.client.get('/api/accounts/users/{}/'.format(self.bob.id))
        self.assertEqual(response.json()['followers_count'], 1)
        self.assertEqual(response.json()['following_count'], 0)


class CommentTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)
        cls.book = Book.objects.create(
            name='Имя ветра', description='.', language='ru', publishing_year=2007,
        )
        cls.other_book = Book.objects.create(
            name='Другая', description='.', language='ru', publishing_year=2010,
        )
        cls.character = Character.objects.create(book=cls.book, name='Квоут')

    def test_create_comment_sets_author_from_request(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/social/comments/', {
            'book': self.book.id, 'text': 'Отличная книга.',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['user']['username'], 'alice')

    def test_cannot_forge_author(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post('/api/social/comments/', {
            'book': self.book.id, 'text': 'Тест', 'user': self.bob.id,
        })
        self.assertEqual(Comment.objects.get().user, self.alice)

    def test_comment_requires_authentication(self):
        response = self.client.post('/api/social/comments/', {
            'book': self.book.id, 'text': 'Аноним',
        })
        self.assertEqual(response.status_code, 401)

    def test_list_returns_top_level_with_nested_replies(self):
        parent = Comment.objects.create(user=self.alice, book=self.book, text='Верхний уровень')
        Comment.objects.create(user=self.bob, book=self.book, parent=parent, text='Ответ')

        response = self.client.get('/api/social/comments/?book={}'.format(self.book.id))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]['replies']), 1)
        self.assertEqual(results[0]['replies'][0]['text'], 'Ответ')

    def test_reply_to_reply_is_rejected(self):
        parent = Comment.objects.create(user=self.alice, book=self.book, text='Первый')
        reply = Comment.objects.create(user=self.bob, book=self.book, parent=parent, text='Второй')

        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/social/comments/', {
            'book': self.book.id, 'parent': reply.id, 'text': 'Третий уровень',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('parent', response.json())

    def test_reply_must_belong_to_same_book(self):
        parent = Comment.objects.create(user=self.alice, book=self.book, text='Первый')
        self.client.force_authenticate(user=self.bob)
        response = self.client.post('/api/social/comments/', {
            'book': self.other_book.id, 'parent': parent.id, 'text': 'Чужая ветка',
        })
        self.assertEqual(response.status_code, 400)

    def test_character_must_belong_to_same_book(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/social/comments/', {
            'book': self.other_book.id, 'character': self.character.id, 'text': 'Не тот герой',
        })
        self.assertEqual(response.status_code, 400)

    def test_author_can_edit_own_comment(self):
        comment = Comment.objects.create(user=self.alice, book=self.book, text='Было')
        self.client.force_authenticate(user=self.alice)
        response = self.client.patch(
            '/api/social/comments/{}/'.format(comment.id), {'text': 'Стало'},
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.text, 'Стало')

    def test_stranger_cannot_edit_or_delete_comment(self):
        comment = Comment.objects.create(user=self.alice, book=self.book, text='Моё')
        self.client.force_authenticate(user=self.bob)

        patch = self.client.patch('/api/social/comments/{}/'.format(comment.id), {'text': 'Взлом'})
        self.assertEqual(patch.status_code, 403)

        delete = self.client.delete('/api/social/comments/{}/'.format(comment.id))
        self.assertEqual(delete.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_staff_can_moderate_comment(self):
        comment = Comment.objects.create(user=self.alice, book=self.book, text='Спам')
        moderator = User.objects.create_user(username='mod', password=PASSWORD, is_staff=True)
        self.client.force_authenticate(user=moderator)
        response = self.client.delete('/api/social/comments/{}/'.format(comment.id))
        self.assertEqual(response.status_code, 204)

    def test_toggle_comment_like(self):
        comment = Comment.objects.create(user=self.alice, book=self.book, text='Текст')
        self.client.force_authenticate(user=self.bob)
        url = '/api/social/comments/{}/toggle_like/'.format(comment.id)

        first = self.client.post(url)
        self.assertTrue(first.json()['liked'])
        self.assertEqual(first.json()['likes_count'], 1)

        second = self.client.post(url)
        self.assertFalse(second.json()['liked'])
        self.assertFalse(CommentLike.objects.exists())

    def test_is_liked_reflects_current_user(self):
        comment = Comment.objects.create(user=self.alice, book=self.book, text='Текст')
        CommentLike.objects.create(user=self.bob, comment=comment)

        anon = self.client.get('/api/social/comments/').json()['results'][0]
        self.assertFalse(anon['is_liked'])
        self.assertEqual(anon['likes_count'], 1)

        self.client.force_authenticate(user=self.bob)
        mine = self.client.get('/api/social/comments/').json()['results'][0]
        self.assertTrue(mine['is_liked'])

    def test_comment_list_query_count_is_flat(self):
        """Ответы и лайки не должны добавлять запрос на каждый комментарий."""
        for i in range(3):
            parent = Comment.objects.create(
                user=self.alice, book=self.book, text='Комментарий {}'.format(i),
            )
            Comment.objects.create(user=self.bob, book=self.book, parent=parent, text='Ответ')

        self.client.force_authenticate(user=self.bob)
        self.client.get('/api/social/comments/')
        with self.assertNumQueries(4):
            self.client.get('/api/social/comments/')

        for i in range(5):
            parent = Comment.objects.create(
                user=self.alice, book=self.book, text='Ещё {}'.format(i),
            )
            Comment.objects.create(user=self.bob, book=self.book, parent=parent, text='Ответ')

        with self.assertNumQueries(4):
            self.client.get('/api/social/comments/')


class IsFollowingFieldTests(APITestCase):
    """
    Кнопка «Подписаться» на фронте берёт состояние из этого поля.
    Если оно врёт, пользователь видит неверную надпись до первого клика.
    """

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='alice', password=PASSWORD)
        cls.bob = User.objects.create_user(username='bob', password=PASSWORD)
        cls.carol = User.objects.create_user(username='carol', password=PASSWORD)
        Follow.objects.create(follower=cls.alice, following=cls.bob)

    def test_true_when_viewer_follows(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/accounts/users/{}/'.format(self.bob.id))
        self.assertTrue(response.json()['is_following'])

    def test_false_when_viewer_does_not_follow(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/accounts/users/{}/'.format(self.carol.id))
        self.assertFalse(response.json()['is_following'])

    def test_false_for_own_profile(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/accounts/users/{}/'.format(self.alice.id))
        self.assertFalse(response.json()['is_following'])

    def test_false_for_anonymous(self):
        response = self.client.get('/api/accounts/users/{}/'.format(self.bob.id))
        self.assertFalse(response.json()['is_following'])

    def test_lists_resolve_the_flag_without_a_query_per_user(self):
        for index in range(8):
            extra = User.objects.create_user(
                username='extra{}'.format(index), password=PASSWORD,
            )
            Follow.objects.create(follower=extra, following=self.bob)

        self.client.force_authenticate(user=self.alice)
        url = '/api/social/users/{}/followers/'.format(self.bob.id)

        self.client.get(url)  # прогрев
        with self.assertNumQueries(4):
            self.client.get(url)
