from flask import Flask
from flask_sqlalchemy import SQLAlchemy #数据库ORM
from flask_bootstrap import Bootstrap   #框架
from flask_login import LoginManager    #登录管理模块
from flask_wtf.csrf import CsrfProtect      #csrf保护模块
from flask_moment import Moment             #时间模块
from config import Config                   #配置文件模块
from flask_mail import Mail
import pymysql
import logging
import time
import os


pymysql.install_as_MySQLdb()
db = SQLAlchemy()
bootstrap = Bootstrap()
moment = Moment()
mail = Mail()

handler=logging.FileHandler('error.log',encoding='UTF-8')
logging_format=logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
handler.setFormatter(logging_format)


login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    CsrfProtect(app)

    app.logger.addHandler(handler)
    db.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
