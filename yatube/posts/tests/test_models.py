from django.conf import settings
from django.test import TestCase

from posts.models import Group, Post, Comment, Follow
from users.forms import User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def test_posts_have_correct_object_names(self):
        post = PostModelTest.post
        expected_object_name = post.text[:settings.TEXT_LENGTH]
        self.assertEqual(expected_object_name, str(post))

    def test_groups_have_correct_object_names(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_comments_have_correct_object_names(self):
        comment = PostModelTest.comment
        expected_object_name = comment.text[:settings.TEXT_LENGTH]
        self.assertEqual(expected_object_name, str(comment))

    def test_follows_have_correct_object_names(self):
        follow = PostModelTest.follow
        expected_object_name = f'Подписка {self.user} на {self.author}'
        self.assertEqual(
            expected_object_name, str(follow))
