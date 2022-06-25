'''
Handles messages from the client to the server.
'''

from abc import ABCMeta, abstractmethod
from enum import Flag, auto
from typing import Type

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from livequiz.models import BuzzEvent, LiveQuizParticipant, LiveQuizView, LiveQuizModel
import livequiz.responses as respond


class UnexpectedMessageException(Exception):
    '''Thrown when a suitable message type is not found.'''

    def __init__(self, msg_type, *args: object) -> None:
        super().__init__(
            f'Unexpected message type {msg_type} encountered.', *args)


class AuthorizationOptions(Flag):
    '''Represents which types of clients can be accepted.'''
    HOST = auto()
    PLAYER = auto()
    ANY = HOST | PLAYER

    @staticmethod
    def from_is_host_boolean(is_host):
        if is_host:
            return AuthorizationOptions.HOST

        return AuthorizationOptions.PLAYER


class AuthorizationException(Exception):
    '''Thrown when an unauthorized socket tries to access a message handler.'''

    def __init__(self, socket_auth, message_auth, *args: object) -> None:
        super().__init__(
            f'Socket is authorized for {socket_auth}, not for {message_auth}')


class MalformedMessageException(Exception):
    '''Thrown when a message cannot be parsed for the given type.'''


class ClientMessage(metaclass=ABCMeta):
    '''
    A generic handler for client messages. Subclass for functionality.
    '''
    _registered_handlers: dict[str, Type['ClientMessage']] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        try:
            key = kwargs.pop('message_key')
        except KeyError as exception:
            raise KeyError(
                'ClientMessage subclass forgot to set "message_key"') from exception

        authorization = kwargs.pop('authorization', AuthorizationOptions.ANY)

        registry = ClientMessage._registered_handlers

        if key in registry:
            raise KeyError(
                f'ClientMessage subclass message_key clash: {cls} and {registry[key]}')

        registry[key] = (authorization, cls)

        super().__init_subclass__(**kwargs)

    @staticmethod
    def get_handler(is_host: bool, msg_type: str) -> Type['ClientMessage']:
        '''Attempts to fetch a suitable handling class.'''
        if not msg_type in ClientMessage._registered_handlers:
            raise UnexpectedMessageException(msg_type)

        authorization, klass = ClientMessage._registered_handlers[msg_type]
        socket_auth = AuthorizationOptions.from_is_host_boolean(is_host)
        if not (socket_auth & authorization):
            raise AuthorizationException(
                socket_auth=socket_auth,
                message_auth=authorization
            )

        return klass

    @staticmethod
    async def handle(socket: AsyncJsonWebsocketConsumer, message: dict, is_host=False) -> None:
        '''
        Passes the given message information to an appropriate handler.'''
        try:
            msg_type = message['type']
            data = message['payload']
        except Exception as exception:
            raise UnexpectedMessageException('format') from exception

        klass = ClientMessage.get_handler(
            is_host,
            msg_type=msg_type)

        handler = klass(data)
        await handler.handle_message(socket)

    @abstractmethod
    async def handle_message(self, socket) -> None:
        '''Attempts to handle the request from the client.'''


class SetViewMessage(
        ClientMessage,
        message_key='set view',
        authorization=AuthorizationOptions.HOST):
    '''Command to set the view of the quiz.'''

    def __init__(self, data):
        try:
            self.view_name = data['view']
            self.question_id = data['question_id']
        except Exception as error:
            raise MalformedMessageException(
                'Expected view and question_id in message.') from error

    async def handle_message(self, socket) -> None:
        new_view_string = await database_sync_to_async(
            lambda code, view, q_id: LiveQuizModel.objects.get(code=code).set_view(
                LiveQuizView(view), q_id
            ))(socket.quiz_code, self.view_name, self.question_id)

        event = {
            'type': 'send_generic_message',
            'data': new_view_string
        }
        await socket.channel_layer.group_send(socket.group_name, event)


class ManageBuzzMessage(
        ClientMessage,
        message_key='manage buzz',
        authorization=AuthorizationOptions.HOST):
    '''When a buzz starts or stops.'''

    def __init__(self, data):
        try:
            self.action = data['action']
            if not self.action in ['start', 'end']:
                raise KeyError('Action must be either "start" or "end"')
        except Exception as error:
            raise MalformedMessageException(
                'Problem getting manage buzz action.'
            ) from error

    async def handle_message(self, socket) -> None:
        match self.action:
            case 'start':
                await self.start_buzz_event(socket)
            case 'end':
                await self.end_buzz_event(socket)

    async def start_buzz_event(self, socket):
        '''Start a new buzz and delete the old.'''
        def refresh_buzz_event(quiz_code):
            quiz = LiveQuizModel.objects.get(code=quiz_code)

            if quiz.buzz_event:
                quiz.buzz_event.delete()

            quiz.buzz_event = BuzzEvent.objects.create()
            quiz.save()

        await database_sync_to_async(refresh_buzz_event)(socket.quiz_code)

        await socket.channel_layer.group_send(
            socket.group_name,
            {
                'type': 'send.generic.message',
                'data': respond.get_buzz_event_message(True)
            }
        )

    async def end_buzz_event(self, socket):
        '''End whatever buzzing was happening.'''
        def delete_buzz_event(quiz_code):
            quiz = LiveQuizModel.objects.get(code=quiz_code)

            if quiz.buzz_event:
                quiz.buzz_event.delete()
            quiz.buzz_event = None
            quiz.save()

        await database_sync_to_async(delete_buzz_event)(socket.quiz_code)

        await socket.channel_layer.group_send(
            socket.group_name,
            {
                'type': 'send.generic.message',
                'data': respond.get_buzz_event_message(False)
            }
        )


class BuzzInMessage(
        ClientMessage,
        message_key='buzz in',
        authorization=AuthorizationOptions.PLAYER):
    '''A player tries to buzz in!'''

    def __init__(self, data) -> None:
        pass

    async def handle_message(self, socket) -> None:
        @database_sync_to_async
        def attempt_buzz_update(quiz_code, socket_name):
            quiz = LiveQuizModel.objects.get(code=quiz_code)
            if not quiz.buzz_event or quiz.buzz_event.player:
                return False, None

            player = LiveQuizParticipant.objects.get(socket_name=socket_name)
            quiz.buzz_event.player = player
            quiz.buzz_event.save()

            return True, player.name

        buzzed_in, name = await attempt_buzz_update(socket.quiz_code, socket.channel_name)

        if buzzed_in:
            await socket.channel_layer.group_send(
                socket.group_name,
                {
                    'type': 'send.generic.message',
                    'data': respond.get_buzz_event_message(
                        True,
                        socket.channel_name,
                        name
                    )
                }
            )
