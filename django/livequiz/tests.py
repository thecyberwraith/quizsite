from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from . import models
from quiz.models import QuizModel


class TestLiveQuizModelCreateForQuizMethod(TestCase):
    '''Isolates tests to the LiveQuizModel'''

    def setUp(self) -> None:
        self.quizA = QuizModel.objects.create(name='A Quiz')
        self.quizB = QuizModel.objects.create(name='B Quiz')

    def test_can_generate_unique_codes(self):
        x = models.LiveQuizModel.create_for_quiz(self.quizA.id)
        y = models.LiveQuizModel.create_for_quiz(self.quizA.id)

        self.assertNotEqual(x.code, y.code)

    @patch.object(models, 'generate_random_slug', return_value='ABCDEFG')
    def test_same_code_cannot_be_shared_between_quizzes(self, _):
        models.LiveQuizModel.create_for_quiz(self.quizA.id)

        with self.assertRaises(DatabaseError):
            models.LiveQuizModel.create_for_quiz(self.quizB.id)

    @patch.object(models, 'generate_random_slug')
    def test_keeps_trying_to_create(self, gen_function):
        codes = ['ABC'] * (models.UNIQUE_RETRIES)
        codes.append('CBA')

        gen_function.side_effect = codes

        models.LiveQuizModel.create_for_quiz(self.quizA.id)

        self.assertEqual(
            models.LiveQuizModel.create_for_quiz(self.quizA.id).code,
            'CBA'
        )


class TestLiveQuizModelRegisterAndUnregister(TestCase):
    def setUp(self):
        self.quiz_id = QuizModel.objects.create(name='A quiz').id

    def test_register_initially_creates(self):
        self.assertEqual(models.LiveQuizModel.objects.count(), 0)

        models.LiveQuizModel.register_for_quiz(self.quiz_id)

        self.assertEqual(models.LiveQuizModel.objects.count(), 1)

    def test_register_does_not_make_copies(self):
        self.assertEqual(models.LiveQuizModel.objects.count(), 0)

        results = [models.LiveQuizModel.register_for_quiz(
            self.quiz_id) for _ in range(10)]

        self.assertEqual(models.LiveQuizModel.objects.count(), 1)
        for i in range(1, 10):
            self.assertEqual(results[0].code, results[i].code)

    def test_unregister_decrements_registered_hosts_count(self):
        for _ in range(6):
            quiz = models.LiveQuizModel.register_for_quiz(self.quiz_id)

        for _ in range(4):
            models.LiveQuizModel.unregister_for_quiz(self.quiz_id)

        self.assertEqual(models.LiveQuizModel.objects.get(
            code=quiz.code).registered_hosts, 2)

    def test_unregister_returns_false_when_registered_hosts_not_zero(self):
        models.LiveQuizModel.register_for_quiz(self.quiz_id)
        models.LiveQuizModel.register_for_quiz(self.quiz_id)
        self.assertFalse(
            models.LiveQuizModel.unregister_for_quiz(self.quiz_id))

    def test_unregister_returns_true_when_registered_hosts_is_zero(self):
        models.LiveQuizModel.register_for_quiz(self.quiz_id)
        self.assertTrue(models.LiveQuizModel.unregister_for_quiz(self.quiz_id))

    def test_unregister_deletes_quiz_when_hosts_is_zero(self):
        code = models.LiveQuizModel.register_for_quiz(self.quiz_id).code
        models.LiveQuizModel.unregister_for_quiz(self.quiz_id)
        with self.assertRaises(models.LiveQuizModel.DoesNotExist):
            models.LiveQuizModel.objects.get(code=code)


class PageBasedTest(TestCase):
    '''A test that gets a page referenced by a reverse tag.'''
    page_url_key = 'nope'
    page_kwargs = None

    def get_response(self):
        '''Perform a get request referenced by 'page_url_key and return the response.'''
        return self.client.get(reverse(self.page_url_key, kwargs=self.page_kwargs))


class TestJoinPage(PageBasedTest):
    page_url_key = 'livequiz:join'

    def test_reachable(self):
        self.assertEqual(self.get_response().status_code, 200)


class TestPlayPage(PageBasedTest):
    page_url_key = 'livequiz:play'
    page_kwargs = {'quiz_code': 'abcde'}

    def test_reachable(self):
        self.assertEqual(self.get_response().status_code, 200)


class TestHostPage(PageBasedTest):
    page_url_key = 'livequiz:host'
    page_kwargs = {'quiz_code': 'abcde'}

    def test_reachable(self):
        self.assertEqual(self.get_response().status_code, 200)
