from __future__ import unicode_literals

import json
import sys

from django.contrib.admin import site
from django.contrib.admin.tests import AdminSeleniumTestCase
from django.contrib.admin.views.main import (
    AutocompleteJsonView, AutocompletePage, AutocompletePaginator,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils.six import text_type

from .admin import AnswerAdmin, QuestionAdmin
from .models import Answer, Question
from .tests import AdminViewBasicTestCase

site.register(Question, QuestionAdmin)
site.register(Answer, AnswerAdmin)


class AutocompleteJsonViewTest(AdminViewBasicTestCase):
    url = reverse_lazy('admin:autocomplete')

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='user', password='secret', email='user@example.com')
        AdminViewBasicTestCase.setUpTestData()

    def test_no_field_identifier(self):
        factory = RequestFactory()
        request = factory.get(self.url)
        request.user = self.superuser
        with self.assertRaisesMessage(PermissionDenied, 'No "field_identifier" provided.'):
            AutocompleteJsonView.as_view(admin_site=site)(request)

    def test_wrong_field_identifier_format(self):
        factory = RequestFactory()
        request = factory.get(self.url, {'field_identifier': 'wrong.format'})
        request.user = self.superuser
        with self.assertRaisesMessage(PermissionDenied, 'Invalid "field_identifier".'):
            AutocompleteJsonView.as_view(admin_site=site)(request)

    def test_not_existing_field_identifier(self):
        factory = RequestFactory()
        request = factory.get(self.url, {'field_identifier': 'foo.bar.baz'})
        request.user = self.superuser
        with self.assertRaisesMessage(PermissionDenied, 'Invalid "field_identifier".'):
            AutocompleteJsonView.as_view(admin_site=site)(request)

    def test_not_model_not_registered(self):
        site.unregister(Question)
        factory = RequestFactory()
        request = factory.get(self.url, {'field_identifier': 'admin_views.Answer.question'})
        request.user = self.superuser
        with self.assertRaisesMessage(
            Http404,
            "<class 'admin_views.models.Question'> is not registered in the admin."
        ):
            AutocompleteJsonView.as_view(admin_site=site)(request)
        site.register(Question, QuestionAdmin)

    def test_success(self):
        q = Question.objects.create(question='Is this a question?')
        factory = RequestFactory()
        request = factory.get(self.url, {'field_identifier': 'admin_views.Answer.question', 'term': 'is'})
        request.user = self.superuser
        response = AutocompleteJsonView.as_view(admin_site=site)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIn({'id': text_type(q.pk), 'text': q.question}, data['results'])

    def test_no_search_fields(self):
        with self.assertRaisesMessage(
            NotImplementedError,
            'The admin for <class \'admin_views.models.Owner\'> needs to implement "search_fields".'
        ):
            self.client.get(reverse_lazy('admin:admin_views_building_add'))

    def test_permission_wrapper(self):
        response = self.client.get(self.url, {'field_identifier': 'admin_views.Answer.question', 'term': ''})
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(self.url, {'field_identifier': 'admin_views.Answer.question', 'term': ''})
        self.assertEqual(response.status_code, 302)

    def test_has_change_permission_denied(self):
        factory = RequestFactory()
        request = factory.get(self.url, {'field_identifier': 'admin_views.Answer.question', 'term': 'is'})
        self.user.is_staff = True
        self.user.save()
        request.user = self.user
        with self.assertRaisesMessage(PermissionDenied, ""):
            AutocompleteJsonView.as_view(admin_site=site)(request)

    def test_has_change_permission_success_with_staff_user(self):
        factory = RequestFactory()
        request = factory.get(self.url, {'field_identifier': 'admin_views.Answer.question', 'term': 'is'})
        p = Permission.objects.filter(codename='change_answer')
        self.user.user_permissions.set(p)
        self.user.is_staff = True
        self.user.save()
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.assertTrue(self.user.has_perm('admin_views.change_answer'))
        request.user = self.user

        response = AutocompleteJsonView.as_view(admin_site=site)(request)
        self.assertEqual(response.status_code, 200)


@override_settings(ROOT_URLCONF='admin_views.urls')
class SeleniumTests(AdminSeleniumTestCase):
    available_apps = ['admin_views'] + AdminSeleniumTestCase.available_apps

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username='super', password='secret', email='super@example.com')
        self.admin_login(username='super', password='secret', login_url=reverse('admin:index'))

    def test_select(self):
        self.selenium.get(self.live_server_url + reverse('admin:admin_views_question_add'))
        elem = self.selenium.find_element_by_css_selector('.select2-selection')
        elem.click()
        results = self.selenium.find_element_by_css_selector('.select2-results')
        self.assertTrue(results.is_displayed())
        elem = results.find_element_by_css_selector('.select2-results__option')
        elem.click()


class AutocompletePaginatorTest(TestCase):

    def setUp(self):
        Question.objects.bulk_create(
            Question(question=text_type(i))
            for i in range(20)
        )

    def test_count(self):
        paginator = AutocompletePaginator(Question.objects.all(), 10)
        self.assertGreater(paginator.count, 10)
        self.assertEqual(paginator.count, sys.maxsize)

        paginator = AutocompletePaginator(Question.objects.none(), 10)
        self.assertEqual(paginator.count, 0)

    def test_validate_number(self):
        paginator = AutocompletePaginator(Question.objects.all(), 10)
        self.assertEqual(paginator.validate_number(1), 1)
        self.assertEqual(paginator.validate_number(2), 2)
        self.assertEqual(paginator.validate_number(3), 3)

    def test__get_page(self):
        paginator = AutocompletePaginator(Question.objects.all(), 10)
        page = paginator.page(1)
        self.assertIsInstance(page, AutocompletePage)


class AutocompletePageTest(TestCase):

    def setUp(self):
        Question.objects.bulk_create(
            Question(question=text_type(i))
            for i in range(20)
        )

    def test_has_next(self):
        paginator = AutocompletePaginator(Question.objects.all(), 10)
        self.assertTrue(paginator.page(1).has_next())
        self.assertTrue(paginator.page(2).has_next())
        self.assertFalse(paginator.page(3).has_next())

        paginator = AutocompletePaginator(Question.objects.all(), 15)
        self.assertTrue(paginator.page(1).has_next())
        self.assertFalse(paginator.page(2).has_next())
