class Config(object):
    DEUBG = False
    TESTING = False
    UPLOAD_FOLDER = r"data\upload"


class DevelopmentConfig(Config):
    DEUBG = True
    SECRET_KEY = 'dev'
    USERNAME = 'dev'
    PASSWORD = 'dev'
