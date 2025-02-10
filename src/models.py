from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class EnvironmentData(db.Model):
    __tablename__ = 'environment_data'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    tide_cycle_hour = db.Column(db.Float, nullable=True)
    tide_cycle_fraction = db.Column(db.Float, nullable=True)
    sun_state = db.Column(db.String(50), nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_direction = db.Column(db.Float, nullable=True)
    cloudcover_low = db.Column(db.Float, nullable=True)
    cloudcover_mid = db.Column(db.Float, nullable=True)
    cloudcover_high = db.Column(db.Float, nullable=True)
