import os

class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY=os.environ.get('SECRET_KEY') or 'string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')