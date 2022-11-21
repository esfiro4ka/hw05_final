from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post
from users.forms import User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.user = User.objects.create(username='Authorized Client')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.PUBLIC_URLS = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            f'/profile/{cls.author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.PRIVATE_URLS = {
            f'/posts/{cls.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/follow/': 'posts/follow.html',
        }
        cls.FOLLOW_URLS = {
            f'/profile/{cls.author}/follow/': f'/auth/login/?next=/profile/{cls.author}/follow/',
            f'/profile/{cls.author}/unfollow/': f'/auth/login/?next=/profile/{cls.author}/unfollow/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_url_exists_at_desired_location_for_author(self):
        """Подписываться и отписываться может авторизованный пользователь."""
        for address in self.FOLLOW_URLS.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertRedirects(response, f'/profile/{self.author}/')

    def test_follow_url_redirects_for_guest_client(self):
        """Подписываться и отписываться не может неавторизованный."""
        for address, redirects in self.FOLLOW_URLS.items():
            with self.subTest(address=address, redirects=redirects):
                response = self.guest_client.get(address)
                self.assertRedirects(response, redirects)

    def test_follow_urls_only_for_author(self):
        """Смотреть ленту подписок может только авторизованный пользователь."""
        response = self.guest_client.get('/follow/')
        self.assertRedirects(
            response, '/auth/login/?next=/follow/'
        )

    def test_public_url_exists_at_desired_location_for_guest_client(self):
        for address in self.PUBLIC_URLS.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url_exists_at_desired_location_for_author(self):
        for address in self.PRIVATE_URLS.keys():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirects_for_guest_client(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_comment_post_detail_only_for_author(self):
        """Комментировать посты может только авторизованный пользователь."""
        response = self.guest_client.get(f'posts/{self.post.id}/comment')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND
        )

    def test_page_url_not_exists_at_desired_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_all_urls_uses_correct_public_template(self):
        for address, template in (list(self.PUBLIC_URLS.items())
                                  + list(self.PRIVATE_URLS.items())):
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
