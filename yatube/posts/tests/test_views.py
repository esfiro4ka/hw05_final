import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, Follow
from users.forms import User

POSTS_AMOUNT_FOR_TEST = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.user = User.objects.create(username='Authorized Client')
        cls.user_2 = User.objects.create(username='Authorized Client 2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded,
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            group=cls.group_2,
            text='Тестовый пост 2',
        )
        cls.PUBLIC_URLS = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html'
        }
        cls.PRIVATE_URLS = {
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        for reverse_name, template in (list(self.PUBLIC_URLS.items())
                                       + list(self.PRIVATE_URLS.items())):
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_public_pages_show_correct_context(self):
        """Шаблоны публичных страниц с правильным контекстом."""
        for address in self.PUBLIC_URLS.keys():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                if 'page_obj' in response.context.keys():
                    first_object = response.context['page_obj'][0]
                else:
                    first_object = response.context['post']
                self.assertEqual(first_object.text, PostsPagesTests.post.text)
                self.assertEqual(
                    first_object.author, PostsPagesTests.post.author
                )
                self.assertEqual(
                    first_object.pub_date, PostsPagesTests.post.pub_date
                )
                self.assertEqual(
                    first_object.group.title, PostsPagesTests.group.title
                )
                self.assertEqual(
                    first_object.group.slug, PostsPagesTests.group.slug
                )
                self.assertEqual(
                    first_object.group.description,
                    PostsPagesTests.group.description
                )
                self.assertIsNotNone(first_object.image)

    def test_group_list_have_correct_filter(self):
        """Список постов group_list отфильтрован по группе."""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(len(response.context['page_obj']), 1)
        """Пост не попал в группу, для которой не был предназначен."""
        response_2 = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'})
        )
        self.assertEqual(len(response_2.context['page_obj']), 1)
        self.assertNotEqual(
            first_object.text, response_2.context['page_obj'][0].text
        )

    def test_profile_have_correct_filter(self):
        """Список постов profile отфильтрован по пользователю."""
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        self.assertEqual(len(response.context['page_obj']), 1)
        """Пост не попал в профайл другого пользователя."""
        response_2 = self.author_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(len(response_2.context['page_obj']), 1)
        self.assertNotEqual(
            response.context['page_obj'][0].text,
            response_2.context['page_obj'][0].text
        )

    def test_post_detail_page_show_correct_context(self):
        """Пост отфильтрован по id."""
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context['post']
        self.assertEqual(first_object.id, PostsPagesTests.post.id)

    def test_private_pages_show_correct_context(self):
        """Шаблоны edit и create сформированы с правильным контекстом."""
        for address in self.PRIVATE_URLS.keys():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertIn('form', response.context.keys())
                self.assertIsInstance(response.context.get('form'), PostForm)

    def test_index_cache(self):
        """Тесты, которые проверяют работу кеша."""
        response_1 = self.author_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_2 = self.author_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(response_2.content, response_3.content)

    def test_404_page_uses_correct_template(self):
        """URL-адрес 404 использует шаблон core/404.html."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_follow_page_uses_template_and_work(self):
        """Страница follow использует правильный шаблон."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertTemplateUsed(response, 'posts/follow.html')
        """"Новая запись автора появляется в ленте тех, кто подписан
        и не появляется в ленте тех, кто не подписан.
        """
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response_1 = self.authorized_client.get(reverse('posts:follow_index'))
        len_by_authorized_client = len(response_1.context['page_obj'])
        response_2 = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        len_by_authorized_client_2 = len(response_2.context['page_obj'])
        Post.objects.create(
            author=self.author,
            group=self.group,
            text='Тестовый пост'
        )
        response_3 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_3.context['page_obj']),
                         len_by_authorized_client + 1)
        response_4 = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_4.context['page_obj']),
                         len_by_authorized_client_2)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts = []
        for post_num in range(POSTS_AMOUNT_FOR_TEST):
            posts.append(
                Post(
                    author=cls.user,
                    group=cls.group,
                    text=f'Тестовый пост {post_num + 1}'
                )
            )
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()
        self.author = Client()
        self.author.force_login(self.user)

    def test_pajinator_first_page(self):
        """Количество постов на первой странице index, group_list и profile."""
        addresses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_AMOUNT
                )

    def test_pajinator_second_page(self):
        """Количество постов на второй странице index, group_list и profile."""
        addresses = [
            reverse('posts:index') + '?page=2',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ) + '?page=2',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ) + '?page=2'
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_AMOUNT_FOR_TEST - settings.POSTS_AMOUNT
                )
