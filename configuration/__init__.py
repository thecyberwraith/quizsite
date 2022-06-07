'''
Aggregate configuration files.
'''
from collections import ChainMap
from importlib import import_module
from os import environ
from pathlib import Path

from .development import generate_config as generate_dev_config


def generate_config(base_dir: Path) -> ChainMap:
    '''
    Creates a chained configuration that gives preference to environment
    variables, then production variables, then development variables.
    '''
    try:
        module = import_module('.production', 'configuration')
        generate_prod_config = module.generate_config
        prod_config = True
        print('Production configuration loaded.')
    except ImportError:
        print('No production configuration detected')
        def generate_prod_config(x): return {}
        prod_config = False

    return ChainMap(
        environ,
        {'DEBUG': not prod_config},
        generate_prod_config(base_dir),
        generate_dev_config(base_dir)
    )
