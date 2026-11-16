"""App settings.

Secrets (passwords, SECRET_KEY) are NOT written here. They are read from a
file called .env next to this one, which git ignores. To set up a new machine,
copy .env.example to .env and fill in the values.
"""
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f'{name} is not set. Copy .env.example to .env and fill in the values.')
    return value


class Config:
    SECRET_KEY = _required('SECRET_KEY')
    ORACLE_USER = _required('ORACLE_USER')
    ORACLE_PASSWORD = _required('ORACLE_PASSWORD')
    ORACLE_DSN = _required('ORACLE_DSN')


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    ORACLE_USER = os.environ.get('ORACLE_TEST_USER', 'studybuddy_test')
    ORACLE_PASSWORD = os.environ.get('ORACLE_TEST_PASSWORD')
