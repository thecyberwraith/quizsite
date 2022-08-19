'''
Contains all responses sent from the server to the client.
'''

from enum import Enum


class MessageTypes(Enum):
    '''The different classes of messages one can send a client.'''
    ERROR = 'error'
    INFO = 'info'
    SET_VIEW = 'set view'
    TERMINATE = 'terminated'
    BUZZ = 'buzz event'
    PLAYER_UPDATE = 'player update'


def get_generic_message(msg_type: MessageTypes, payload: object):
    '''
    The general format for a message sent to the client.
    '''
    return {
        'type': msg_type.value,
        'payload': payload
    }


def get_current_quiz_view_message(view, view_data):
    '''
    Sets what the client should be looking at.
    '''
    return get_generic_message(
        MessageTypes.SET_VIEW,
        {
            'view': view,
            'data': view_data
        }
    )


def get_error_message(errors: list[str]):
    '''
    Just sends a list of error messages.
    '''
    return get_generic_message(
        MessageTypes.ERROR,
        errors
    )


def get_info_message(msg: str):
    '''
    Sends a message which is not necessarily bad!
    '''
    return get_generic_message(
        MessageTypes.INFO,
        msg
    )


def get_terminate_message():
    '''
    Sends the message that the quiz is over.'''
    return get_generic_message(
        MessageTypes.TERMINATE,
        {}
    )


def get_buzz_event_message(exists: bool, player_socket=None, player_name=None):
    '''Either respond none, open, closed with appropriate info for closed.'''
    if not exists:
        payload = {
            'status': 'none'
        }
    elif player_socket is None:
        payload = {
            'status': 'open'
        }
    else:
        payload = {
            'status': 'closed',
            'socket': player_socket,
            'name': player_name
        }

    return get_generic_message(
        MessageTypes.BUZZ,
        payload
    )

def get_player_update_message(socket_name, new_name):
    '''Just tell them the new name.'''
    return get_generic_message(
        MessageTypes.PLAYER_UPDATE,
        {'name': new_name, 'socket': socket_name}
    )