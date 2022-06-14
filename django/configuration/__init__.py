'''
Aggregate configuration files.
'''
from collections import ChainMap
from importlib import import_module
from logging import Logger
from os import environ
from pathlib import Path

LOG = Logger(__name__)


def get_hostname() -> str:
    '''Attempt to read the SERVER_HOST_NAME environment variable.'''
    try:
        return environ['SERVER_HOST_NAME']
    except KeyError:
        LOG.warning(
            "No 'SERVER_HOST_NAME' environment variable present. Defaulting to localhost.")
        return 'localhost'


def get_debug() -> bool:
    '''Attempt to read 'yes' or 'true' from the DEBUG environment variable.'''

    try:
        debug = environ['DEBUG']
    except KeyError:
        LOG.warning(
            "No 'DEBUG' environment variable present. Defaulting to true.")
        debug = 'true'

    return debug.lower() in ['yes', 'true']


def get_secret() -> str:
    '''Attempt to read the SECRET environment variable.'''

    try:
        return environ['SECRET']
    except KeyError:
        LOG.warning(
            "No 'SECRET' environment variable present. Defaulting to a terribly insecure secret.")
        return 'NOSECRETSHERE'


def generate_config(_: Path) -> dict:
    '''
    Creates a chained configuration that gives preference to environment
    variables, then production variables, then development variables.
    '''
    config = {
        'SERVER_HOST_NAME': get_hostname(),
        'DEBUG': get_debug(),
        'SECRET_KEY': get_secret()
    }

    return config
