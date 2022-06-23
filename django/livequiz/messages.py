'''
Handles messages from the client to the server.
'''

from abc import ABCMeta, abstractmethod
from typing import Type

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from livequiz.models import LiveQuizModel


class UnexpectedMessageException(Exception):
    '''Thrown when a suitable message type is not found.'''

    def __init__(self, msg_type, *args: object) -> None:
        super().__init__(
            f'Unexpected message type {msg_type} encountered.', *args)


class HostOnlyException(Exception):
    '''Thrown when a non-host attempts to send a host only message.'''

    def __init__(self, *args: object) -> None:
        super().__init__('Cannot use this message type: reserved for hosts only.')


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

        host_only = kwargs.pop('host_only', False)

        registry = ClientMessage._registered_handlers

        if key in registry:
            raise KeyError(
                f'ClientMessage subclass message_key clash: {cls} and {registry[key]}')

        registry[key] = (host_only, cls)

        super().__init_subclass__(**kwargs)

    @staticmethod
    def get_handler(is_host: bool, msg_type: str) -> Type['ClientMessage']:
        '''Attempts to fetch a suitable handling class.'''
        if not msg_type in ClientMessage._registered_handlers:
            raise UnexpectedMessageException(msg_type)

        host_only, klass = ClientMessage._registered_handlers[msg_type]

        if host_only and not is_host:
            raise HostOnlyException()

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
    async def handle_message(self, socket, data: dict) -> None:
        '''Attempts to handle the request from the client.'''


class SetViewMessage(ClientMessage, message_key='set_view', host_only=True):
    '''Command to set the view of the quiz.'''

    def __init__(self, data):
        try:
            self.view_name = data['view']
            self.question_id = data['question_id']
        except Exception as error:
            raise MalformedMessageException(
                'Expected view and question_id in message.') from error

    async def handle_message(self, socket, data: dict) -> None:
        new_view_string = database_sync_to_async(
            lambda code, view, q_id: LiveQuizModel.objects.get(code=code).set_view(
                view, q_id
            ))(socket.quiz_code, self.view_name, self.question_id)

        await socket.channel_layer.group_send(
            socket.group_name,
            {
                'type': 'set_view',
                'view_data': {
                    'view': self.view_name,
                    'data': new_view_string
                }
            }
        )
