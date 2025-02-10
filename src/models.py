from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # New flag for admin users

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin
        }

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
    
    # Associate each record with a user.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('environment_data', lazy=True))
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "tide_cycle_hour": self.tide_cycle_hour,
            "tide_cycle_fraction": self.tide_cycle_fraction,
            "sun_state": self.sun_state,
            "temperature": self.temperature,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "cloudcover_low": self.cloudcover_low,
            "cloudcover_mid": self.cloudcover_mid,
            "cloudcover_high": self.cloudcover_high,
            "user_id": self.user_id,
        }
