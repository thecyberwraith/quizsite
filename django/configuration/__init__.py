'''
Aggregate configuration files.
'''
from collections import ChainMap
from importlib import import_module
from os import environ
from pathlib import Path

def generate_config(base_dir: Path) -> ChainMap:
    '''
    Creates a chained configuration that gives preference to environment
    variables, then production variables, then development variables.
    '''
    return {
        'HOSTNAME': environ['HOSTNAME'],
        'DEBUG': environ['DEBUG'].lower() in ['yes', 'true'],
        'SECRET_KEY': environ['SECRET']
    }