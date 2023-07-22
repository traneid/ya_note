from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestFormVisible(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Писатель')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.url_add = reverse('notes:add')
        cls.form_data = {'title': 'Заголовок',
                         'text': 'Текст',
                         'slug': '01', }

    def test_authorized_client_has_form(self):
        """Залогиненый пользователь видит форму для заметки"""
        self.client.force_login(self.author)
        response = self.client.get(self.url_add)
        self.assertIn('form', response.context)

    def test_notes_in_list_for_author(self):
        """Заметка передается в лист автора"""
        response = self.author_client.post(self.url_add, data=self.form_data)
        response = self.author_client.get(reverse('notes:list'))
        obj_list = response.context['object_list']
        note = Note.objects.get()
        self.assertIn(note, obj_list)

    def test_note_not_in_list_for_another_user(self):
        """Заметка не попадает в лист другого автора"""
        response = self.author_client.post(self.url_add, data=self.form_data)
        response = self.reader_client.get(reverse('notes:list'))
        obj_list = response.context['object_list']
        note = Note.objects.get()
        self.assertNotIn(note, obj_list)