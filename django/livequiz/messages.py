'''
Contains methods for parsing and creating messages on the server side for a live quiz.
'''
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class MalformedMessageException(Exception):
    '''Thrown when a ClientMessage subclass was not able to handle the given data.'''
    pass


class UnexpectedMessageType(Exception):
    '''Thrown when no suitable message parser exists.'''
    pass


class ClientMessage:
    '''
    Creates a python object for a message coming from the client.

    Subclasses must handle the data dictionary from a message in their constructor and
    throw a 'MalformedMessageException' if it is not formatted properly.

    Handling the consequences of a message are left to the 'handle_message' method.
    '''
    _message_map = {}

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, 'MESSAGE_KEY'):
            raise Exception(
                f'All subclasses must specify a message key. Check {cls}.')
        if cls.MESSAGE_KEY in cls._message_map:
            raise Exception(
                f'Class message keys clash: {cls} and {cls._message_map[cls.MESSAGE_KEY]}.')

        cls._message_map[cls.MESSAGE_KEY] = cls

    async def handle_message(self, socket: AsyncJsonWebsocketConsumer) -> None:
        '''Perform asynchronous actions to fulfill the message request.'''
        pass

    @staticmethod
    async def handle_client_message(socket: AsyncJsonWebsocketConsumer, message_type: str, data: dict) -> None:
        '''Hands the given data for a specified message type to the appropriate class'''
        if message_type not in ClientMessage._message_map:
            raise UnexpectedMessageType(f'{message_type} is not handled.')

        parser = ClientMessage._message_map[message_type](data)
        await parser.handle_message(socket)


class PlayerUpdateRequest(ClientMessage):
    MESSAGE_KEY = 'update player'


class HostChangeViewRequest(ClientMessage):
    MESSAGE_KEY = 'change view'


class CurrentViewRequest(ClientMessage):
    MESSAGE_KEY = 'request view update'


def send_current_view(socket: AsyncJsonWebsocketConsumer, view_data):
    '''Sends a message with the current view.'''