class Config(object):
    DEUBG = False
    TESTING = False
    UPLOAD_FOLDER = r"data\upload"
    CMJ_COMP_URL = r"http://127.0.0.1:5001/cmj/compute"


class DevelopmentConfig(Config):
    DEUBG = True
    SECRET_KEY = 'dev'
    USERNAME = 'dev'
    PASSWORD = '$2b$12$Z35iGkzVHNlZ8jtGPAFLGOZOPn1yedmtrd3ZZ2njWyERsZ7gIHyZe'
    CMJ_COMP_URL = r"http://127.0.0.1:5001/cmj/compute"

