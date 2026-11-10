class Config:
    SECRET_KEY = 'change-me-in-production'
    ORACLE_USER = 'studybuddy'
    ORACLE_PASSWORD = 'studybuddy'
    ORACLE_DSN = 'localhost:1521/XEPDB1'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    ORACLE_USER = 'studybuddy_test'
