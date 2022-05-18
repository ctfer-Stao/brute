from flask import Flask
from flask_sqlalchemy import SQLAlchemy
class BayonetConfig(object):
    '''Flask数据配置'''
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:hxz1314520@127.0.0.1/bayonet?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
APP = Flask(__name__)
APP.config.from_object(BayonetConfig)
DB = SQLAlchemy(APP)
