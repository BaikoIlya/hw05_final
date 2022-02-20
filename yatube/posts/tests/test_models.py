from django.test import TestCase

from ..models import Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа больше 15 символов',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Должно получится после среза: Должно получитс',
        )

    def test_models_have_correct_object_names(self):
        """Проверка правильности имён моделей"""
        post = PostModelTest.post
        group = PostModelTest.group
        correct_names = {
            str(post): post.text[:15],
            str(group): group.title
        }
        for current_name, correct_name in correct_names.items():
            with self.subTest():
                self.assertEqual(current_name, correct_name, 'incorrect name')
