'''
Contains all responses sent from the server to the client.
'''

from enum import Enum
from livequiz.models import LiveQuizModel

class MessageTypes(Enum):
    '''The different classes of messages one can send a client.'''
    ERROR = 'error'
    INFO = 'info'
    SET_VIEW = 'set view'

def get_generic_message(msg_type: MessageTypes, payload: object):
    '''
    The general format for a message sent to the client.
    '''
    return {
        'type': msg_type.value,
        'payload': payload
    }

def get_current_quiz_view_message(command):
    '''
    Sets what the client should be looking at.
    '''
    return get_generic_message(
        MessageTypes.SET_VIEW,
        command
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