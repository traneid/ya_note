from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import TestCase

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.author = User.objects.create(username='Писатель')
        cls.reader = User.objects.create(username='Читатель')

        cls.notes = Note.objects.create(title='Заголовок',
                                        text='Текст',
                                        slug='01',
                                        author=cls.author)

    def test_pages_availability(self):
        """Тестирование страниц доступных анонимному пользователю"""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_detail_page(self):
        """Тестирование доступа автора к отдельной записи"""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit',
                         'notes:delete',
                         'notes:detail',):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.notes.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_list_add_sucsess_page(self):
        """Тестирование пользователя к списку заметок, странице добавления"""
        users_statuses = (
            (self.reader, HTTPStatus.OK),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:list',
                         'notes:add',
                         'notes:success',):
                with self.subTest(user=user, name=name):
                    url = reverse(name)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client01(self):
        """Тестирование перенаправления анонимных пользователей
        со страниц отдельных записей"""
        login_url = reverse('users:login')
        for name in ('notes:edit',
                     'notes:delete',
                     'notes:detail',):
            with self.subTest(name=name):
                url = reverse(name, args=(self.notes.slug,))
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_redirect_for_anonymous_client02(self):
        """Тестирование перенаправления анонимных пользователей
        со страниц общих записей"""
        login_url = reverse('users:login')
        for name in ('notes:list',
                     'notes:add',
                     'notes:success',):
            with self.subTest(name=name):
                url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)