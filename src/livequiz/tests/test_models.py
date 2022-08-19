from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.db import DatabaseError
from django.test import TestCase

import livequiz.models as module


class TestLiveQuizManagerCreateForQuizMethod(TestCase):
    '''Isolates tests to the LiveQuizManager'''
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = module.User.objects.create_user(username='x', password='y')

    def create_empty_quiz(self):
        return module.LiveQuizModel.objects.create_for_quiz(
            self.user,
            module.QuizData(name='Test', categories={}),
        )

    def test_can_generate_unique_codes(self):
        x = self.create_empty_quiz()
        y = self.create_empty_quiz()

        self.assertNotEqual(x.code, y.code)

    @patch.object(module, 'generate_random_slug', return_value='ABCDEFG')
    def test_same_code_cannot_be_shared_between_quizzes(self, _):
        self.create_empty_quiz()

        with self.assertRaises(DatabaseError):
            self.create_empty_quiz()

    @patch.object(module, 'generate_random_slug')
    def test_keeps_trying_to_create(self, gen_function):
        codes = ['ABC'] * (module.UNIQUE_RETRIES)
        codes.append('CBA')

        gen_function.side_effect = codes

        self.create_empty_quiz()

        self.assertEqual(
            self.create_empty_quiz().code,
            'CBA'
        )

    def test_initializes_last_view_to_quiz_board(self):
        model = module.LiveQuizModel.objects.create_for_quiz(
            self.user,
            module.QuizData(name='Test', categories={
                'Test': (
                    (100, 'Who am I?', 'Me'),
                )
            }),
        )

        q_id = module.LiveQuizQuestion.objects.get(question='Who am I?').pk

        self.assertEqual(
            model.last_view_command,
            {
                'type': 'set view',
                'payload': {
                    'view': module.LiveQuizView.QUIZ_BOARD.value,
                    'data': {
                        'Test': [
                            {
                                'id': q_id,
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
        cls.quiz = module.LiveQuizModel.objects.create_for_quiz(
            module.User.objects.create_user(username='?', password='??'),
            module.QuizData(name='Test', categories=
                {
                    'Poetry': (
                        (100, 'Knock?', 'Knock.'),
                    ),
                    'Math': (
                        (200, '1+1', '2'),
                        (400, '4*9', '36'),
                    )
                }
            ),
        )

        cls.q1 = module.LiveQuizQuestion.objects.get(question='Knock?').pk
        cls.q2 = module.LiveQuizQuestion.objects.get(question='1+1').pk
        cls.q3 = module.LiveQuizQuestion.objects.get(question='4*9').pk

    def test_set_view_to_quiz_board_return_value(self):
        self.quiz.answered_questions = [self.q2]

        result = self.quiz.set_view(module.LiveQuizView.QUIZ_BOARD)

        self.assertEqual(
            result,
            {
                'type': 'set view',
                'payload': {
                    'view': module.LiveQuizView.QUIZ_BOARD.value,
                    'data': {
                        'Poetry': [
                            {
                                'id': self.q1,
                                'value': 100
                            },
                        ],
                        'Math': [
                            None,
                            {
                                'id': self.q3,
                                'value': 400
                            }
                        ]
                    }
                }
            }
        )

    def test_set_view_to_question_result(self):
        result = self.quiz.set_view(
            module.LiveQuizView.QUESTION,
            question=self.q1
        )

        self.assertEqual(
            result,
            {
                'type': 'set view',
                'payload': {
                    'view': module.LiveQuizView.QUESTION.value,
                    'data':
                    {
                        'id': self.q1,
                        'text': 'Knock?'
                    }
                }
            }
        )

    def test_set_view_to_answer_result(self):
        result = self.quiz.set_view(
            module.LiveQuizView.ANSWER,
            question=self.q2
        )

        self.assertEqual(
            result,
            {
                'type': 'set view',
                'payload': {
                    'view': module.LiveQuizView.ANSWER.value,
                    'data': {
                        'id': self.q2,
                        'text': '1+1',
                        'answer': '2'
                    }
                }
            }
        )


class TestLiveQuizManagerOwnedByMethod(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.host1 = module.User.objects.create_user(username='bob', password='a')
        cls.host2 = module.User.objects.create_user(username='linda', password='b')
        cls.quiz1 = module.LiveQuizModel.objects.create_for_quiz(cls.host1, module.QuizData(name='Test', categories={}))
        cls.quiz2 = module.LiveQuizModel.objects.create_for_quiz(cls.host2, module.QuizData(name='Test', categories={}))
        cls.quiz3 = module.LiveQuizModel.objects.create_for_quiz(cls.host1, module.QuizData(name='Test', categories={}))

    def test_returns_all_quizzes_owned(self):
        self.assertSetEqual(
            set(module.LiveQuizModel.objects.owned_by_user(self.host1)),
            set([self.quiz1, self.quiz3])
        )
    
    def test_returns_none_for_anonymous(self):
        self.assertEqual(
            module.LiveQuizModel.objects.owned_by_user(AnonymousUser()),
            []
        )


class TestLiveQuizManagerDeleteMethod(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.host1 = module.User.objects.create_user(username='x', password='y')
        cls.quiz1 = module.LiveQuizModel.objects.create_for_quiz(
            cls.host1,
            module.QuizData(name='Test', categories={})
        )
    
    def test_delete_quiz(self):
        self.quiz1.delete()
        
        with self.assertRaises(module.LiveQuizModel.DoesNotExist):
            module.LiveQuizModel.objects.get(code=self.quiz1.code)
    
    def test_sends_terminate(self):
        with patch.object(module, 'async_to_sync') as mock:
            group_name = self.quiz1.group_name
            self.quiz1.delete()
            mock.assert_called_once_with(module.get_channel_layer().group_send)
            mock.return_value.assert_called_once_with(
                group_name,
                {
                    'type': 'quiz.terminated'
                }
            )
        

class TestLiveQuizParticipantManagerRegistration(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = module.User.objects.create_user(username='x', password='y')
        cls.quiz = module.LiveQuizModel.objects.create_for_quiz(
            cls.user,
            module.QuizData(name='Test', categories={})
        )

    def test_register_creates_first(self):
        self.assertEqual(0, module.LiveQuizParticipant.objects.all().count())
        
        module.LiveQuizParticipant.objects.register_socket(
            self.quiz,
            new_socket_name='socket a',
            old_socket_name=None
        )

        module.LiveQuizParticipant.objects.get(socket_name='socket a')

    def test_register_replaces_socket(self):
        pk = module.LiveQuizParticipant.objects.register_socket(
            self.quiz,
            new_socket_name='socket a',
            old_socket_name=None
        ).pk

        module.LiveQuizParticipant.objects.register_socket(
            self.quiz,
            new_socket_name='socket c',
            old_socket_name='socket a'
        )

        result = module.LiveQuizParticipant.objects.get(socket_name='socket c')
        
        self.assertEqual(pk, result.pk)

        with self.assertRaises(module.LiveQuizParticipant.DoesNotExist):
            module.LiveQuizParticipant.objects.get(socket_name='socket a')