'''
Handles messages from the client to the server.
'''

from abc import ABCMeta, abstractmethod
from typing import Type

from livequiz.consumers import LiveQuizConsumer


class UnexpectedMessageException(Exception):
    '''Thrown when a suitable message type is not found.'''

    def __init__(self, msg_type, *args: object) -> None:
        super().__init__(
            f'Unexpected message type {msg_type} encountered.', *args)


class MalformedMessageException(Exception):
    '''Thrown when a message cannot be parsed for the given type.'''


class ClientMessage(metaclass=ABCMeta):
    '''
    A generic handler for client messages. Subclass for functionality.
    '''
    _registered_handlers: dict[str, Type['ClientMessage']] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        key = getattr(cls, 'MESSAGE_KEY', None)
        registry = ClientMessage._registered_handlers

        if key is None:
            raise NameError(
                f'Client Message Subclass {cls} is missing MESSAGE_KEY.')

        if key in registry:
            raise KeyError(
                f'Client Message subclass message key clash: {cls} and {registry[key]}')

        ClientMessage._registered_handlers[key] = cls

    @staticmethod
    def get_handler(msg_type: str) -> Type['ClientMessage']:
        '''Attempts to fetch a suitable handling class.'''
        if not msg_type in ClientMessage._registered_handlers:
            raise UnexpectedMessageException(msg_type)

        return ClientMessage._registered_handlers[msg_type]

    @staticmethod
    async def handle(socket: LiveQuizConsumer, message: dict) -> None:
        '''
        Passes the given message information to an appropriate handler.'''
        try:
            msg_type = message['type']
            data = message['payload']
        except Exception as exception:
            raise UnexpectedMessageException('format') from exception

        klass = ClientMessage.get_handler(msg_type=msg_type)
        handler = klass(data)
        await handler.handle_message(socket, data)

    @abstractmethod
    async def handle_message(self, socket, data: dict) -> None:
        '''Attempts to handle the request from the client.'''
