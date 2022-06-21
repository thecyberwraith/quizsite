from enum import Enum
import logging as LOG

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import User

from livequiz.messages import ClientMessage
from livequiz.models import LiveQuizModel
from livequiz.responses import get_error_message, get_info_message


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
    def __init__(self, *args, **kwargs):
        self.quiz_code = None
        self.live_quiz = None

        super().__init__(*args, **kwargs)

    async def connect(self):
        await self.accept()

        self.quiz_code = self.scope['url_route']['kwargs']['quiz_code']
        socket_user = self.scope['user']

        errors = await self.find_connect_errors(socket_user, self.quiz_code)

        if errors:
            LOG.warning('Errors encountered when host connected to quiz [%s]:\n%s',
                        self.quiz_code,
                        errors)
            await self.send_json(get_error_message(errors))
            await self.close()
            return

        await self.on_successful_connect()
    
    async def find_connect_errors(self, _: User, quiz_code: str) -> list[str]:
        '''
        Performs checks before a socket is allowed to continue connecting. The default is to
        verify that the quiz exists. If it does, self.live_quiz is set to it.

        Connection should happen if no errors are found (an empty list is returned)
        '''
        try:
            self.live_quiz = await database_sync_to_async(
                lambda code: LiveQuizModel.objects.get(code=quiz_code)
            )(quiz_code)

        except LiveQuizModel.DoesNotExist:
            return ['The specified live quiz does not exist.']
        
        return []
    
    async def on_successful_connect(self):
        '''
        Only called if no errors were found when calling 'find_connect_errors'. By
        default, attaches to the live quiz group.
        '''
        await self.channel_layer.group_add(
            self.live_quiz.group_name,
            self.channel_name
        )
    
    async def disconnect(self, code):
        if self.live_quiz is not None:
            await self.channel_layer.group_discard(
                self.live_quiz.group_name,
                self.channel_name
            )

        return await super().disconnect(code)

    async def receive_json(self, content, **kwargs):
        await ClientMessage.handle(self, content, False)


class LiveQuizHostConsumer(LiveQuizConsumer):
    '''
    Represents the connection to a host who is currently running a live quiz.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    async def receive_json(self, content, **kwargs):
        await ClientMessage.handle(self, content, is_host=True)

    async def find_connect_errors(self, user: User, quiz_code: str):
        '''In addition to parent method, checks for authentication and ownership.'''
        errors = await super().find_connect_errors(user, quiz_code)

        if not user.is_authenticated:
            errors.append('Only authenticated users can host a quiz.')

        if errors:
            return errors

        owner = await database_sync_to_async(
            lambda livequiz: livequiz.quiz.owner
        )(self.live_quiz)

        if owner != user:
            errors.append('You are not the owner of the quiz.')
        else:
            self.user = user

        return errors

    async def disconnect(self, code):
        await super().disconnect(code)

        LOG.info('Host disconnecting from live quiz %s with code %s',
                 self.quiz_code,
                 code)

        return await super().disconnect(code)

    async def on_successful_connect(self):
        await super().on_successful_connect()
        await self.send_json(get_info_message('Connected successfully.'))
        LOG.debug('Host successfully connect to quiz %s', self.quiz_code)

        


class LiveQuizParticipantConsumer(LiveQuizConsumer):
    '''Consumers for participants of quizzes.'''
    async def look_for_errors(self, user: User, quiz_code: str) -> list[str]:
        old_socket = self.scope['session'].get('socketname', None)
        self.scope['session']['socketname'] = self.channel_name
