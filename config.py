import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # CSRF protection, Flask-WTF use this secret key to generate encrypted token
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Mario will give u a SECRET_KEY'
    # enable automatic commits of database changes at the end of each request
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # The tested PM's work dir
    WORK_DIR = os.environ.get('WORK_DIR') or '/mario'
    # The tested PM's moosefs mount point
    MFS_MOUNT_POINT = os.environ.get('MFS_MOUNT_POINT') or '/mnt/mfs/'
    MFS_MASTER = os.environ.get('MFS_MASTER') or '10.214.144.233'



    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    BOOTSTRAP_SERVE_LOCAL = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
