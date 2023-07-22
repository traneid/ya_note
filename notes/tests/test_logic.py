from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Заголовок'
    NOTE_SLUG = '01'
    NOTE_TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.reader = User.objects.create(username='Читатель')
        cls.url_add = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.reader)
        cls.form_data = {'title': cls.NOTE_TITLE,
                         'text': cls.NOTE_TEXT,
                         'slug': cls.NOTE_SLUG}

    def test_anonymous_user_cant_create_note(self):
        """Аноним не может отправить заметку"""
        self.client.post(self.url_add, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_comment(self):
        """Зарегистрированный пользователь может оставить заметку"""
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.reader)

    def test_empty_slug(self):
        """Тестирование добавления заметки с пустым слагом"""
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestCommentEditDelete(TestCase):
    NOTE_TITLE = 'Заголовок'
    NOTE_TITLE_NEW = 'Новый заголовок'
    NOTE_TEXT = 'Текст'
    NOTE_TEXT_NEW = 'Новый Текст'
    NOTE_SLUG = '01'
    NOTE_SLUG_NEW = '02'

    @classmethod
    def setUpTestData(cls):
        cls.url_add = reverse('notes:add')
        cls.url_to_success = reverse('notes:success')
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.notes = Note.objects.create(title=cls.NOTE_TITLE,
                                        text=cls.NOTE_TEXT,
                                        slug=cls.NOTE_SLUG,
                                        author=cls.author)
        cls.edit_url = reverse('notes:edit', args=(cls.notes.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.notes.slug,))
        cls.form_data = {'title': cls.NOTE_TITLE_NEW,
                         'text': cls.NOTE_TEXT_NEW,
                         'slug': cls.NOTE_SLUG_NEW, }

    def test_author_can_delete_comment(self):
        """Тестирование удаления комментария автором"""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_success)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        """Тестирование невозможноcти удаления чужой записи"""
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_comment(self):
        """Тестирование возможности редактирования записи автором"""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_to_success)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.NOTE_TEXT_NEW)
        self.assertEqual(self.notes.title, self.NOTE_TITLE_NEW)
        self.assertEqual(self.notes.slug, self.NOTE_SLUG_NEW)

    def test_user_cant_edit_comment_of_another_user(self):
        """Тестирование невозможности редактирования записи неавтором"""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.NOTE_TEXT)
        self.assertEqual(self.notes.title, self.NOTE_TITLE)
        self.assertEqual(self.notes.slug, self.NOTE_SLUG)

    def test_user_cant_use_bad_words(self):
        """Тестирование невозможности отправки заметки с одинаковым слагом"""
        bad_note = {'title': self.NOTE_TITLE_NEW,
                    'text': self.NOTE_TEXT_NEW,
                    'slug': self.NOTE_SLUG, }
        response = self.author_client.post(self.url_add, data=bad_note)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.notes.slug + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)