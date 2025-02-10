from celery_app import celery
from models import db, EnvironmentData
from api_calls.tide_cycle import TideStation
from api_calls.weather import WeatherAPI
from api_calls.suntimes import SunTimeAPI
import json

@celery.task(name='fetch_env_data')
def fetch_env_data(record_id):
    """Fetch environmental data for a given timestamp and coordinates."""
    env_data = EnvironmentData.query.get(record_id)
    if not env_data:
        print(f"Record ID {record_id} not found.")
        return

    try:
        print(f"Processing environment data for record {record_id}")

        # 1. SunTime API Call: use coordinates from env_data
        try:
            sun_api = SunTimeAPI(lat=env_data.latitude, lng=env_data.longitude)
            sun_state = sun_api.get_time_of_day(env_data.timestamp)
            env_data.sun_state = sun_state
            print(f"SunTime API Success: {sun_state}")
        except Exception as e:
            print(f"SunTime API Error: {e}")
            env_data.status = 'error'
            db.session.commit()
            return

        # 2. Weather API Call: use coordinates from env_data
        try:
            weather_api = WeatherAPI(lat=env_data.latitude, lng=env_data.longitude)
            weather_data = weather_api.get_weather_summary(env_data.timestamp, env_data.latitude, env_data.longitude)
            if weather_data:
                env_data.temperature = float(weather_data.get("temperature_2m (°C)", 0.0))
                env_data.wind_speed = float(weather_data.get("wind_speed_10m (km/h)", 0.0))
                env_data.wind_direction = float(weather_data.get("wind_direction_10m (°)", 0.0))
                env_data.cloudcover_low = float(weather_data.get("cloudcover_low (%)", 0.0))
                env_data.cloudcover_mid = float(weather_data.get("cloudcover_mid (%)", 0.0))
                env_data.cloudcover_high = float(weather_data.get("cloudcover_high (%)", 0.0))
                print(f"Weather API Success: {json.dumps(weather_data, indent=2)}")
            else:
                print("Weather API returned no data.")
                env_data.status = 'error'
                db.session.commit()
                return
        except Exception as e:
            print(f"Weather API Error: {e}")
            env_data.status = 'error'
            db.session.commit()
            return

        # 3. Tide Cycle API Call: use coordinates from env_data
        try:
            # Read API key from file.
            with open('api_calls/tide_api_key') as f:
                api_key = f.read().strip()

            tide_station = TideStation(api_key=api_key)
            fraction, hours = tide_station.get_current_tide_cycle(lat=env_data.latitude,
                                                                  lon=env_data.longitude,
                                                                  now_dt=env_data.timestamp)
            env_data.tide_cycle_fraction = fraction
            env_data.tide_cycle_hour = hours
            print(f"Tide Cycle API Success: Fraction={fraction}, Hours={hours}")
        except Exception as e:
            print(f"Tide Cycle API Error: {e}")
            env_data.status = 'error'
            db.session.commit()
            return

        env_data.status = 'complete'
        print(f"Task for record {record_id} completed successfully.")
        db.session.commit()
    except Exception as e:
        print(f"General Task Error: {e}")
        db.session.rollback()
        env_data.status = 'error'
        db.session.commit()
