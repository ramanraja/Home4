import os
base_dir = os.path.dirname(os.path.abspath(__file__))

class Config (object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '!my--secret-key!'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or ('sqlite:///' + os.path.join(base_dir,  'mydb.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HUB_ID = os.environ.get('HUB_ID') or 'My_Hub1.0'
    
    