from enum import Enum
import logging as LOG

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.views import View

from livequiz.models import LiveQuizModel
from quiz.models import QuizModel


def get_error_message(messages):
    '''Returns a dictionary containing the error message.'''
    return {
        'error': {
            'message': messages
        }
    }


def get_success_message():
    '''Returns a dictionary with a success message.'''
    return {
        'message': 'Successfully connected.'
    }


class Actions(Enum):
    '''Represents possible actions that can be sent over the channels.'''
    SET_VIEW = 'set_view'


class Views(Enum):
    '''Represents possible views that can be seen.'''
    QUIZ = 'quiz'
    QUESTION = 'question'
    ANSWER = 'answer'


class LiveQuizState:
    '''Represents the state of the quiz. Generates messages.'''

    def __init__(self, quiz: QuizModel):
        self.quiz = quiz
        self.scores = {}
        self.answered_questions = {}

    @database_sync_to_async
    def get_quiz_view_message(self):
        '''
        Returns the message to see the overall quiz and gives which
        questions are unanswered.
        '''
        available_questions = {}
        for category in self.quiz.categories.all():
            q_list = []
            for question in category.questions.all():
                if question.id in self.answered_questions:
                    q_list.append(None)
                else:
                    q_list.append(question.value)

        return {
            'action': Actions.SET_VIEW.name,
            'view': Views.QUIZ.name,
            'categories': available_questions
        }


@database_sync_to_async
def get_quiz_and_owner(quiz_code):
    '''Synchronously get the quiz and its owner from the database.'''
    livequiz = LiveQuizModel.objects.get(code=quiz_code)
    return livequiz.quiz, livequiz.quiz.owner


class LiveQuizHostConsumer(AsyncJsonWebsocketConsumer):
    '''
    Represents the connection to a host who is currently running a live quiz.
    '''
    async def connect(self):
        await self.accept()

        self.quiz_code = self.scope['url_route']['kwargs']['quiz_code']
        self.user = self.scope['user']
        self.group_name = None

        errors = await self.look_for_connect_errors()

        if errors:
            LOG.warning('Errors encountered when setting up live quiz[%s]:\n%s',
                        self.quiz_code,
                        errors)
            await self.send_json(get_error_message(errors))
            await self.close()
            return

        LOG.info('Starting live quiz %s', self.quiz_code)
        await self.send_json(get_success_message())

        await self.setup_quiz()

    async def look_for_connect_errors(self):
        errors = []

        if not self.user.is_authenticated:
            errors.append('Only authenticated users can host a quiz.')
        else:
            try:
                self.quiz, owner = await get_quiz_and_owner(self.quiz_code)
                if owner != self.user:
                    errors.append('You are not the owner of the quiz.')
            except LiveQuizModel.DoesNotExist:
                errors.append(
                    'The specified quiz is not live. Try launching it.')

        return errors

    async def disconnect(self, code):
        LOG.info('Host disconnecting from live quiz %s with code %s',
                 self.quiz_code,
                 code)

        return await super().disconnect(code)

    async def setup_quiz(self):
        '''
        Attaches (creates) to the channel group for this quiz and
        sends the first instructions.
        '''
        self.state = LiveQuizState(self.quiz)

        self.group_name = f'livequiz_{self.quiz_code}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_to_all',
                'payload': await self.state.get_quiz_view_message()
            }
        )

    async def send_to_all(self, event):
        await self.send_json(event['payload'])


class LiveQuizParticipantConsumer(AsyncJsonWebsocketConsumer):
    '''Consumers for participants of quizzes.'''

    async def connect(self, quiz_code):
        await self.accept()
        try:
            self.quiz, _ = await get_quiz_and_owner(quiz_code)
        except LiveQuizModel.DoesNotExist:
            await self.send_json(get_error_message(['Quiz does not exist!']))
            self.close()

        old_socket = self.scope['session'].get('socketname', None)
        self.scope['session']['socketname'] = self.channel_name

    async def disconnect(self, code):
        return await super().disconnect(code)
