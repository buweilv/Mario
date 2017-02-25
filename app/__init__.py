from flask import Flask
from flask_bootstrap import Bootstrap
#from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from config import config, Config
import redis

bootstrap = Bootstrap()
#moment = Moment()
db = SQLAlchemy()
socketio = SocketIO()
pool = redis.ConnectionPool(host='localhost', port=6379, db=5)
conn = redis.Redis(connection_pool=pool)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
#    moment.init_app(app)
    db.init_app(app)

    socketio.init_app(app, async_mode=Config.ASYNC_MODE)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
