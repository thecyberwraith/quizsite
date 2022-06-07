from pathlib import Path

def generate_config(base_dir: Path) -> dict:
    '''Public configuration for testing.'''
    return {
        'SECRET_KEY': 'chdt*1588zi!(0l(_@7r60ld=ka541x-oj9*$+g6vn)b-%@*-_',
        'HOSTS': [],
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': base_dir/ 'db.sqlite3',
            }
        }
    }
