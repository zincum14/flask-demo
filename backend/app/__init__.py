from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import redis
from minio import Minio
from config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    jwt.init_app(app)

    # 初始化Redis客户端
    app.redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASSWORD']
    )

    # 初始化MinIO客户端
    app.minio_client = Minio(
        app.config['MINIO_ENDPOINT'],
        access_key=app.config['MINIO_ACCESS_KEY'],
        secret_key=app.config['MINIO_SECRET_KEY'],
        secure=False
    )

    # 注册蓝图
    from .routes import auth, posts, comments, users
    app.register_blueprint(auth.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(comments.bp)
    app.register_blueprint(users.bp)

    return app 