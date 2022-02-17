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
        post_name = str(post)
        correct_post_name = post.text[:15]
        self.assertEqual(post_name, correct_post_name, 'incorrect Post name')
        group_name = str(group)
        correct_group_name = group.title
        self.assertEqual(
            group_name, correct_group_name, 'incorrect Group name'
        )
