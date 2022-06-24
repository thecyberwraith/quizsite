from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

import livequiz.models as models
from quiz.models import CategoryModel, QuizModel


class TestLiveQuizModelCreateForQuizMethod(TestCase):
    '''Isolates tests to the LiveQuizModel'''

    def setUp(self) -> None:
        self.quizA = QuizModel.objects.create(name='A Quiz')
        self.quizB = QuizModel.objects.create(name='B Quiz')

    def test_can_generate_unique_codes(self):
        x = models.LiveQuizModel.objects.create_for_quiz(self.quizA.id)
        y = models.LiveQuizModel.objects.create_for_quiz(self.quizA.id)

        self.assertNotEqual(x.code, y.code)

    @patch.object(models, 'generate_random_slug', return_value='ABCDEFG')
    def test_same_code_cannot_be_shared_between_quizzes(self, _):
        models.LiveQuizModel.objects.create_for_quiz(self.quizA.id)

        with self.assertRaises(DatabaseError):
            models.LiveQuizModel.objects.create_for_quiz(self.quizB.id)

    @patch.object(models, 'generate_random_slug')
    def test_keeps_trying_to_create(self, gen_function):
        codes = ['ABC'] * (models.UNIQUE_RETRIES)
        codes.append('CBA')

        gen_function.side_effect = codes

        models.LiveQuizModel.objects.create_for_quiz(self.quizA.id)

        self.assertEqual(
            models.LiveQuizModel.objects.create_for_quiz(self.quizA.id).code,
            'CBA'
        )

    def test_initializes_last_view_to_quiz_board(self):
        category = self.quizA.categories.create(name='Test')
        q_id = category.questions.create(
            question_text='Who am',
            solution_text='I?',
            value=100
        )

        model = models.LiveQuizModel.objects.create_for_quiz(self.quizA.id)

        self.assertEqual(
            model.last_view_command,
            {
                'type': 'set view',
                'payload': {
                    'view': models.LiveQuizView.QUIZ_BOARD.value,
                    'data': {
                        'Test': [
                            {
                                'id': q_id.id,
                                'value': 100
                            }
                        ]
                    }
                }
            }
        )


class TestLiveQuizModelSetViewMethod(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.quiz = QuizModel.objects.create(name='A Quiz')
        category = cls.quiz.categories.create(name='Poetry')
        cls.question_ids = []
        cls.question_ids.append([q.pk for q in [
            category.questions.create(
                value=100,
                question_text='To be?',
                solution_text='Or not to be?'
            ),
            category.questions.create(
                value=200,
                question_text='Knock?',
                solution_text='Knock'
            )
        ]
        ])

        category = cls.quiz.categories.create(name='Math')
        cls.question_ids.append([q.pk for q in [
            category.questions.create(
                value=100,
                question_text='1+1',
                solution_text='2'
            )
        ]])

        cls.livequiz = models.LiveQuizModel.objects.create_for_quiz(
            cls.quiz.id)

    def test_set_view_to_quiz_board_return_value(self):
        self.livequiz.answered_questions = [self.question_ids[0][1]]

        result = self.livequiz.set_view(models.LiveQuizView.QUIZ_BOARD)

        self.assertEqual(
            result,
            {
                'type': 'set view',
                'payload': {
                    'view': models.LiveQuizView.QUIZ_BOARD.value,
                    'data': {
                        'Poetry': [{
                            'id': self.question_ids[0][0],
                            'value': 100
                        },
                            None,
                        ],
                        'Math': [{
                            'id': self.question_ids[1][0],
                            'value': 100
                        }]
                    }
                }
            }
        )

    def test_set_view_to_question_result(self):
        result = self.livequiz.set_view(
            models.LiveQuizView.QUESTION,
            question=self.question_ids[0][1]
        )

        self.assertEqual(
            result,
            {
                'type': 'set view',
                'payload': {
                    'view': models.LiveQuizView.QUESTION.value,
                    'data':
                    {
                        'id': self.question_ids[0][1],
                        'text': 'Knock?'
                    }
                }
            }
        )

    def test_set_view_to_answer_result(self):
        result = self.livequiz.set_view(
            models.LiveQuizView.ANSWER,
            question=self.question_ids[1][0]
        )

        self.assertEqual(
            result,
            {
                'type': 'set view',
                'payload': {
                    'view': models.LiveQuizView.ANSWER.value,
                    'data': {
                        'id': self.question_ids[1][0],
                        'text': '1+1',
                        'answer': '2'
                    }
                }
            }
        )
