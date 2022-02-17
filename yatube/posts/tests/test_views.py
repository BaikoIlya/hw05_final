import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follow = User.objects.create_user(username='follow')
        cls.user_auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            id=1,
            text='Test text',
            author=cls.user_auth,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.follow_client = Client()
        self.authorized_client.force_login(self.user_auth)
        self.follow_client.force_login(self.user_follow)

    def test_pages_uses_correct_template(self):
        """Проверка правильности шаблона"""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user_auth.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Проверка правильного содержимого главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        post_data = response.context['page_obj'][0]
        self.assertEqual(post_data, self.post)
        self.assertEqual(post_data.image, self.post.image)

    def test_group_posts_correct_context(self):
        """Проверка правильного содержания страницы группы"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertIn('page_obj', response.context)
        post_data = response.context['page_obj'][0]
        self.assertEqual(post_data, self.post)
        self.assertEqual(post_data.image, self.post.image)
        self.assertIn('group', response.context)
        group_data = response.context['group']
        self.assertEqual(group_data, self.post.group)

    def test_post_detail_correct_context(self):
        """Проверка правильно содержания страницы поста"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIn('post', response.context)
        post_data = response.context['post']
        self.assertEqual(post_data, self.post)
        self.assertEqual(post_data.image, self.post.image)
        self.assertIn('cnt', response.context)
        cnt_data = response.context['cnt']
        self.assertEqual(cnt_data, 1)

    def test_profile_correct_context(self):
        """Проверка правильного содержания страницы автора"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user_auth.username}
            )
        )
        self.assertIn('page_obj', response.context)
        post_data = response.context['page_obj'][0]
        self.assertEqual(post_data, self.post)
        self.assertEqual(post_data.image, self.post.image)
        self.assertIn('auth', response.context)
        user_data = response.context['auth']
        self.assertEqual(user_data.username, self.user_auth.username)
        self.assertIn('cnt', response.context)
        cnt_data = response.context['cnt']
        self.assertEqual(cnt_data, 1)

    def test_post_create_correct_context(self):
        """Проверка правильности полей формы при создании"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Проверка правильности полей формы при редактировании"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        post_data = response.context['post']
        self.assertEqual(post_data, self.post)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertIn('form', response.context)
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post(self):
        """Проверка содержимого поля текст тестового поста"""
        text = 'Test text'
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        post_data = response.context['page_obj'][0]
        self.assertEqual(post_data.text, text)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertIn('page_obj', response.context)
        post_data = response.context['page_obj'][0]
        self.assertEqual(post_data.text, text)
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user_auth.username}
            )
        )
        self.assertIn('page_obj', response.context)
        post_data = response.context['page_obj'][0]
        self.assertEqual(post_data.text, text)

    def test_cache_index_page(self):
        """Тестирование использование кеширования"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)

    def test_follow_correct(self):
        """Тестирование возможности подписки и отписки"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_follow.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_auth, author=self.user_follow
            ).exists()
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_follow.username})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_auth, author=self.user_follow
            ).exists()
        )

    def test_correct_follows_posts(self):
        """Тестирование появление новой записи в избранном"""
        test_follow = Follow.objects.create(
            user=self.user_auth,
            author=self.user_follow
        )
        form_data = {
            'text': 'Текст поста подписки',
            'group': self.group.id,
        }
        self.follow_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn('page_obj', response.context)
        self.assertEqual(
            response.context['page_obj'][0], Post.objects.latest('pub_date')
        )
        test_follow.delete()
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
        )
        number_of_posts = 13
        for test_post in range(number_of_posts):
            cls.post = Post.objects.create(
                id=test_post,
                text='Test text',
                author=cls.user_auth,
                group=cls.group
            )
        cls.cnt_first_page = 10
        cls.cnt_second_page = 3

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)

    def test_first_page_contains_ten_posts(self):
        """Проверка что на первой странице 10 записей"""
        templates_page_names = {
            reverse('posts:index'): self.cnt_first_page,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): self.cnt_first_page,
            reverse(
                'posts:profile', kwargs={'username': self.user_auth.username}
            ): self.cnt_first_page,
        }
        for reverse_name, count in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)

    def test_second_page_contains_three_posts(self):
        """Проверка что на второй странице 3 записи"""
        templates_page_names = {
            reverse('posts:index') + '?page=2': self.cnt_second_page,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2': self.cnt_second_page,
            reverse(
                'posts:profile', kwargs={'username': self.user_auth.username}
            ) + '?page=2': self.cnt_second_page,
        }
        for reverse_name, count in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)
