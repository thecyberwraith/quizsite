import logging as LOG

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import User

import livequiz.responses as respond
from livequiz.messages import ClientMessage
from livequiz.models import LiveQuizModel, LiveQuizParticipant


@database_sync_to_async
def get_quiz_and_host(code):
    '''Synchronously get the live quiz and its owner from the database.'''
    livequiz = LiveQuizModel.objects.get(code=code)
    return livequiz, livequiz.host


class LiveQuizConsumer(AsyncJsonWebsocketConsumer):
    '''
    Generic consumer for LiveQuiz interactions that utilizes the messages and reponses
    module.
    '''

    def __init__(self, *args, **kwargs):
        self.code = None
        self.group_name = None
        self._is_host = False

        super().__init__(*args, **kwargs)

    async def connect(self):
        await self.accept()

        self.code = self.scope['url_route']['kwargs']['quiz_code']
        socket_user = self.scope['user']

        values, errors = await self.find_connect_errors(socket_user, self.code)

        if errors:
            LOG.warning('Errors encountered when host connected to quiz [%s]:\n%s',
                        self.code,
                        errors)
            await self.send_json(respond.get_error_message(errors))
            await self.close()
            return

        await self.on_successful_connect(values)

    async def find_connect_errors(self, _: User, quiz_code: str) -> tuple[dict, list[str]]:
        '''
        Performs checks before a socket is allowed to continue connecting. The list contain
        messages of things that went wrong when connecting. The dict contains important values
        that are required for setup and conveniently access during error checking.

        The default is to verify that the quiz exists. If it does, live_quiz is set to it in the
        returned dictionary.

        Connection should happen if no errors are found (an empty list is returned)
        '''
        try:
            live_quiz = await database_sync_to_async(
                lambda code: LiveQuizModel.objects.get(code=quiz_code)
            )(quiz_code)

        except LiveQuizModel.DoesNotExist:
            return {}, ['The specified live quiz does not exist.']

        return {'live_quiz': live_quiz}, []

    async def on_successful_connect(self, values: dict):
        '''
        Only called if no errors were found when calling 'find_connect_errors'. By
        default, attaches to the live quiz group. The values dictionary contains any
        useful values from setup (returned by 'find_connect_errors').
        '''
        self.code = values['live_quiz'].code
        self.group_name = values['live_quiz'].group_name

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.send_json(respond.get_info_message('Connected successfully.'))
        await self.send_generic_message({'data': values['live_quiz'].last_view_command})

        @database_sync_to_async
        def get_buzz_info(quiz):
            event = quiz.buzz_event
            name, socket = None, None
            if event and event.player:
                name, socket = event.player.name, event.player.socket_name

            return event, name, socket

        event, name, socket = await get_buzz_info(values['live_quiz'])
        await self.send_generic_message({'data': respond.get_buzz_event_message(event, socket, name)})

    async def disconnect(self, code):
        if self.group_name is not None:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

        return await super().disconnect(code)

    async def receive_json(self, content, **kwargs):
        try:
            await ClientMessage.handle(self, content, self._is_host)
        except Exception as error:
            response = f'Failed to handle message {content}: {error}'
            LOG.exception(response)
            await self.send_generic_message({'data': respond.get_error_message([response])})

    async def send_generic_message(self, event):
        '''Send the view data to the client.'''
        await self.send_json(event['data'])

    async def quiz_terminated(self, _: dict):
        '''Send the terminate message'''
        await self.send_json(respond.get_terminate_message())
        await self.close()


class LiveQuizHostConsumer(LiveQuizConsumer):
    '''
    Represents the connection to a host who is currently running a live quiz.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_host = True

    async def find_connect_errors(self, user: User, quiz_code: str):
        '''In addition to parent method, checks for authentication and ownership.'''
        values, errors = await super().find_connect_errors(user, quiz_code)

        if not user.is_authenticated:
            errors.append('Only authenticated users can host a quiz.')

        if errors:
            return values, errors

        owner = await database_sync_to_async(
            lambda livequiz: livequiz.host
        )(values['live_quiz'])

        if owner != user:
            errors.append('You are not the owner of the quiz.')
        else:
            values['user'] = user

        return values, errors

    async def disconnect(self, code):
        await super().disconnect(code)

        LOG.info('Host disconnecting from live quiz %s with code %s',
                 self.code,
                 code)

        return await super().disconnect(code)

    async def on_successful_connect(self, values: dict):
        await super().on_successful_connect(values)
        LOG.debug('Host successfully connect to quiz %s', self.code)


class LiveQuizParticipantConsumer(LiveQuizConsumer):
    '''Consumers for participants of quizzes.'''
    async def on_successful_connect(self, values: dict):
        await super().on_successful_connect(values)

        old_socket = self.scope['session'].get('socketname', None)
        self.scope['session']['socketname'] = self.channel_name

        await sync_to_async(lambda session: session.save())(self.scope['session'])

        @database_sync_to_async
        def get_player_info(quiz, new_name, old_name):
            player = LiveQuizParticipant.objects.register_socket(
                quiz, new_name, old_name)
            return player.name

        name = await get_player_info(values['live_quiz'], self.channel_name, old_socket)

        LOG.info(
            f'Player connected claiming socket {old_socket} to {self.channel_name}')

        await self.send_generic_message({'data': respond.get_player_update_message(self.channel_name, name)})
