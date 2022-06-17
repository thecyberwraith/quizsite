from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

import livequiz.models as models
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

    def test_register_makes_unique_copies(self):
        self.assertEqual(models.LiveQuizModel.objects.count(), 0)

        results = [models.LiveQuizModel.register_for_quiz(
            self.quiz_id) for _ in range(10)]

        codes = {result.code for result in results}

        self.assertEqual(len(codes), 10)

    def test_unregister_deletes_quiz(self):
        code = models.LiveQuizModel.register_for_quiz(self.quiz_id).code
        models.LiveQuizModel.unregister(code)
        with self.assertRaises(models.LiveQuizModel.DoesNotExist):
            models.LiveQuizModel.objects.get(code=code)
