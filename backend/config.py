import os

class Config:
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # MySQL配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'password'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'blog'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None

    # MinIO配置
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT') or 'localhost:9000'
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY') or 'minioadmin'
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY') or 'minioadmin'
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET') or 'blog'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 