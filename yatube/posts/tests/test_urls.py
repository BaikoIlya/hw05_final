from http import HTTPStatus
from django.test import TestCase, Client

from ..models import Post, Group, User


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        """Проверка работоспособности страницы"""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about(self):
        """Проверка работоспособности страницы"""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech(self):
        """Проверка работоспособности страницы"""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_auth = User.objects.create_user(username='auth')
        cls.user_some = User.objects.create_user(username='some')
        cls.post = Post.objects.create(
            id=100,
            text='Test text',
            author=cls.user_auth,
        )
        cls.group = Group.objects.create(
            title='test group',
            slug='testslug',
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user_auth.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',

        }
        cls.templates_url_login = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_some)
        self.authorized_client_auth = Client()
        self.authorized_client_auth.force_login(self.user_auth)

    def test_urls_correct_guest(self):
        """Проверка шаблонов для не авторизованного пользователя"""
        for url, template in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK, 'не авторизован'
                )
                self.assertTemplateUsed(response, template)

    def test_urls_correct_authorized(self):
        """Проверка шаблонов для авторизованного пользователя"""
        for url, template in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK, 'авторизован'
                )
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Проверка шаблона не существующей страницы, ошибка 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND, 'не авторизован'
        )
        self.assertTemplateUsed(response, 'core/404.html')
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND, 'авторизован'
        )
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_correct_login_guest(self):
        """Проверка корректного редиректа"""
        for url, template in self.templates_url_login.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, f'/auth/login/?next={url}'
                )

    def test_urls_correct_login_authorized_author(self):
        """Проверка корректного редиректа автора"""
        for url, template in self.templates_url_login.items():
            with self.subTest(url=url):
                response = self.authorized_client_auth.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK, 'авторизован'
                )
                self.assertTemplateUsed(response, template)

    def test_urls_correct_login_not_author(self):
        """Проверка корректного редиректа не автора"""
        for url, template in self.templates_url_login.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                if url == '/create/':
                    self.assertEqual(
                        response.status_code, HTTPStatus.OK, 'не автор'
                    )
                    self.assertTemplateUsed(response, template)
                else:
                    self.assertRedirects(
                        response, f'/posts/{self.post.id}/'
                    )
