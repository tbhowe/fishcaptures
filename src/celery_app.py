from celery import Celery
from flask import Flask
from models import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost:5432/postgres'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app

flask_app = create_app()

celery = Celery(
    flask_app.import_name,
    broker=flask_app.config['CELERY_BROKER_URL'],
    backend=flask_app.config['CELERY_RESULT_BACKEND'],
    include=['tasks']  # 👈 Ensure tasks are auto-discovered
)

celery.conf.update(flask_app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return super().__call__(*args, **kwargs)

celery.Task = ContextTask

# Explicitly import tasks to register with Celery
import tasks  # 👈 Add this line
