import shutil
import tempfile
from http import HTTPStatus
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            id=1,
            text='Some text',
            author=cls.user_auth,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)

    def test_correct_post_create(self):
        """Проверка создания нового поста"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='guest.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Текст формы',
            'group': self.group.id,
            'image': uploaded
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='auth.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Текст формы',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        current_post = Post.objects.latest('pub_date')
        self.assertEqual(
            current_post.text, form_data['text']
        )
        self.assertEqual(
            current_post.group, self.group
        )
        self.assertEqual(
            current_post.author, self.user_auth
        )
        self.assertEqual(
            current_post.image, f'posts/{uploaded.name}'
        )

    def test_correct_post_text_edit(self):
        """Проверка правильного редактирования существующего поста"""
        form_data = {
            'text': 'Change text',
            'group': '',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        current_post = Post.objects.latest('pub_date')
        self.assertEqual(
            current_post.text, form_data['text']
        )
        self.assertIsNone(current_post.group)
        self.assertEqual(Post.objects.filter(group=self.group).count(), 0)

    def test_correct_comment_create(self):
        """Проверка создания комментария под постом"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Comment text'
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(
            response.context['comments'][0], Comment.objects.latest('created')
        )
