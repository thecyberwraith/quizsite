from enum import Enum
import logging as LOG

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from livequiz.messages import ClientMessage
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


@database_sync_to_async
def get_quiz_and_owner(quiz_code):
    '''Synchronously get the live quiz and its owner from the database.'''
    livequiz = LiveQuizModel.objects.get(code=quiz_code)
    return livequiz, livequiz.quiz.owner


class LiveQuizConsumer(AsyncJsonWebsocketConsumer):
    '''
    Generic consumer for LiveQuiz interactions that utilizes the messages and reponses
    module.
    '''
    async def receive_json(self, content, **kwargs):
        await ClientMessage.handle(self, content, False)


class LiveQuizHostConsumer(LiveQuizConsumer):
    '''
    Represents the connection to a host who is currently running a live quiz.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code, self.livequiz, self.user, self.group_name = None, None, None, None

    async def receive_json(self, content, **kwargs):
        await ClientMessage.handle(self, content, is_host=True)

    async def connect(self):
        await self.accept()

        self.quiz_code = self.scope['url_route']['kwargs']['quiz_code']
        self.user = self.scope['user']
        self.group_name = None

        errors = await self.look_for_connect_errors(self.quiz_code)

        if errors:
            LOG.warning('Errors encountered when host connected to quiz [%s]:\n%s',
                        self.quiz_code,
                        errors)
            await self.send_json(get_error_message(errors))
            await self.close()
            return

        LOG.info('Host joining live quiz %s', self.quiz_code)
        await self.send_json(get_success_message())

        await self.setup_quiz()

    async def look_for_connect_errors(self, quiz_code):
        errors = []

        if not self.user.is_authenticated:
            errors.append('Only authenticated users can host a quiz.')
        else:
            try:
                self.livequiz, owner = await get_quiz_and_owner(quiz_code)
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
        self.group_name = self.livequiz.group_name

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )


class LiveQuizParticipantConsumer(LiveQuizConsumer):
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
