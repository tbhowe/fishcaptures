from celery_app import celery
from models import db, EnvironmentData
from api_calls.tides import TideAPIClient
from api_calls.weather import WeatherAPIClient
from api_calls.astronomy import AstronomyAPIClient
import json

@celery.task(name='fetch_env_data')
def fetch_env_data(record_id):
    """
    Fetch environmental data from tide, weather, and astronomy APIs for a given EnvironmentData record.
    
    The task updates the record with:
      - Tide API data: currentTideHeight, tideHour, maxHighTide, minLowTide.
      - Weather API data: airTemperature, pressure, cloudCover, currentDirection, currentSpeed,
        swellDirection, swellHeight, swellPeriod, secondarySwellPeriod, secondarySwellDirection,
        secondarySwellHeight, waveDirection, waveHeight, wavePeriod, windWaveDirection,
        windWaveHeight, windWavePeriod, windDirection, windSpeed, gust.
      - Astronomy API data: sunrise, sunset, moonrise, moonset, moonFraction,
        currentMoonPhaseText, currentMoonPhaseValue, lightLevel.
    
    After all data are updated, the record status is set to "complete".
    """
    env_data = EnvironmentData.query.get(record_id)
    if not env_data:
        print(f"Record ID {record_id} not found.")
        return

    try:
        print(f"Processing environment data for record {record_id}")
        
        # 1. Tide API
        tide_client = TideAPIClient()
        tide_data = tide_client.get_tide_data(env_data.timestamp, env_data.latitude, env_data.longitude)
        if tide_data:
            env_data.currentTideHeight = tide_data.get("currentTideHeight")
            env_data.tideHour = tide_data.get("tideHour")
            env_data.maxHighTide = tide_data.get("maxHighTide")
            env_data.minLowTide = tide_data.get("minLowTide")
            print(f"Tide API data: {tide_data}")
        else:
            print("Tide API returned no data.")
        
        # 2. Weather API
        weather_client = WeatherAPIClient()
        weather_data = weather_client.get_weather_data(env_data.timestamp, env_data.latitude, env_data.longitude)
        if weather_data:
            env_data.airTemperature = weather_data.get("airTemperature")
            env_data.pressure = weather_data.get("pressure")
            env_data.cloudCover = weather_data.get("cloudCover")
            env_data.currentDirection = weather_data.get("currentDirection")
            env_data.currentSpeed = weather_data.get("currentSpeed")
            env_data.swellDirection = weather_data.get("swellDirection")
            env_data.swellHeight = weather_data.get("swellHeight")
            env_data.swellPeriod = weather_data.get("swellPeriod")
            env_data.secondarySwellPeriod = weather_data.get("secondarySwellPeriod")
            env_data.secondarySwellDirection = weather_data.get("secondarySwellDirection")
            env_data.secondarySwellHeight = weather_data.get("secondarySwellHeight")
            env_data.waveDirection = weather_data.get("waveDirection")
            env_data.waveHeight = weather_data.get("waveHeight")
            env_data.wavePeriod = weather_data.get("wavePeriod")
            env_data.windWaveDirection = weather_data.get("windWaveDirection")
            env_data.windWaveHeight = weather_data.get("windWaveHeight")
            env_data.windWavePeriod = weather_data.get("windWavePeriod")
            env_data.windDirection = weather_data.get("windDirection")
            env_data.windSpeed = weather_data.get("windSpeed")
            env_data.gust = weather_data.get("gust")
            print(f"Weather API data: {json.dumps(weather_data, indent=2)}")
        else:
            print("Weather API returned no data.")
        
        # 3. Astronomy API
        astronomy_client = AstronomyAPIClient()
        astronomy_data = astronomy_client.get_astronomy_data(env_data.timestamp, env_data.latitude, env_data.longitude)
        if astronomy_data:
            env_data.sunrise = astronomy_data.get("sunrise")
            env_data.sunset = astronomy_data.get("sunset")
            env_data.moonrise = astronomy_data.get("moonrise")
            env_data.moonset = astronomy_data.get("moonset")
            env_data.moonFraction = astronomy_data.get("moonFraction")
            env_data.currentMoonPhaseText = astronomy_data.get("currentMoonPhaseText")
            env_data.currentMoonPhaseValue = astronomy_data.get("currentMoonPhaseValue")
            env_data.lightLevel = astronomy_data.get("lightLevel")
            print(f"Astronomy API data: {astronomy_data}")
        else:
            print("Astronomy API returned no data.")
        
        env_data.status = "complete"
        print(f"Task for record {record_id} completed successfully.")
        db.session.commit()
    
    except Exception as e:
        print(f"General Task Error: {e}")
        db.session.rollback()
        env_data.status = "error"
        db.session.commit()
