import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID  # Use this if you're on PostgreSQL
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    # Use a UUID for primary key.
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin
        }

class EnvironmentData(db.Model):
    __tablename__ = 'environment_data'
    
    # Primary key as UUID.
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    
    # Tide API fields:
    currentTideHeight = db.Column(db.Float, nullable=True)
    tideHour = db.Column(db.Float, nullable=True)
    maxHighTide = db.Column(db.Float, nullable=True)
    minLowTide = db.Column(db.Float, nullable=True)
    
    # Weather API fields:
    airTemperature = db.Column(db.Float, nullable=True)
    pressure = db.Column(db.Float, nullable=True)
    cloudCover = db.Column(db.Float, nullable=True)
    currentDirection = db.Column(db.Float, nullable=True)
    currentSpeed = db.Column(db.Float, nullable=True)
    swellDirection = db.Column(db.Float, nullable=True)
    swellHeight = db.Column(db.Float, nullable=True)
    swellPeriod = db.Column(db.Float, nullable=True)
    secondarySwellPeriod = db.Column(db.Float, nullable=True)
    secondarySwellDirection = db.Column(db.Float, nullable=True)
    secondarySwellHeight = db.Column(db.Float, nullable=True)
    waveDirection = db.Column(db.Float, nullable=True)
    waveHeight = db.Column(db.Float, nullable=True)
    wavePeriod = db.Column(db.Float, nullable=True)
    windWaveDirection = db.Column(db.Float, nullable=True)
    windWaveHeight = db.Column(db.Float, nullable=True)
    windWavePeriod = db.Column(db.Float, nullable=True)
    windDirection = db.Column(db.Float, nullable=True)
    windSpeed = db.Column(db.Float, nullable=True)
    gust = db.Column(db.Float, nullable=True)
    
    # Astronomy API fields:
    sunrise = db.Column(db.String, nullable=True)
    sunset = db.Column(db.String, nullable=True)
    moonrise = db.Column(db.String, nullable=True)
    moonset = db.Column(db.String, nullable=True)
    moonFraction = db.Column(db.Float, nullable=True)
    currentMoonPhaseText = db.Column(db.String, nullable=True)
    currentMoonPhaseValue = db.Column(db.Float, nullable=True)
    lightLevel = db.Column(db.String, nullable=True)
    
    # Foreign key to User.
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('environment_data', lazy=True))
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            # Tide API fields:
            "currentTideHeight": self.currentTideHeight,
            "tideHour": self.tideHour,
            "maxHighTide": self.maxHighTide,
            "minLowTide": self.minLowTide,
            # Weather API fields:
            "airTemperature": self.airTemperature,
            "pressure": self.pressure,
            "cloudCover": self.cloudCover,
            "currentDirection": self.currentDirection,
            "currentSpeed": self.currentSpeed,
            "swellDirection": self.swellDirection,
            "swellHeight": self.swellHeight,
            "swellPeriod": self.swellPeriod,
            "secondarySwellPeriod": self.secondarySwellPeriod,
            "secondarySwellDirection": self.secondarySwellDirection,
            "secondarySwellHeight": self.secondarySwellHeight,
            "waveDirection": self.waveDirection,
            "waveHeight": self.waveHeight,
            "wavePeriod": self.wavePeriod,
            "windWaveDirection": self.windWaveDirection,
            "windWaveHeight": self.windWaveHeight,
            "windWavePeriod": self.windWavePeriod,
            "windDirection": self.windDirection,
            "windSpeed": self.windSpeed,
            "gust": self.gust,
            # Astronomy API fields:
            "sunrise": self.sunrise,
            "sunset": self.sunset,
            "moonrise": self.moonrise,
            "moonset": self.moonset,
            "moonFraction": self.moonFraction,
            "currentMoonPhaseText": self.currentMoonPhaseText,
            "currentMoonPhaseValue": self.currentMoonPhaseValue,
            "lightLevel": self.lightLevel,
            "user_id": str(self.user_id)
        }
