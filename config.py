import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class Config(object):
    BASE_DIR = dirname(__file__)
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAGE_LIMIT = 10
    DEFAULT_PAGE = 1


class DevelopmentConfiguration(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class TestingConfiguration(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI  = "sqlite:///" + Config.BASE_DIR \
                              + "/test/test_db.sqlite"
    PAGE_LIMIT = 3


app_configuration = {
    'production': Config,
    'development': DevelopmentConfiguration,
    'testing': TestingConfiguration
}
