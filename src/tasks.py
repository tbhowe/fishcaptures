# from celery_app import celery
# from models import db, EnvironmentData
# from api_calls.tide_cycle import TideStation
# from api_calls.weather import WeatherAPI
# from api_calls.suntimes import SunTimeAPI
# import requests
# import json

# @celery.task(name='fetch_env_data')
# def fetch_env_data(record_id):
#     """ Fetch environmental data for a given timestamp. """
#     env_data = EnvironmentData.query.get(record_id)
#     if not env_data:
#         print(f"Record ID {record_id} not found.")
#         return

#     try:
#         print(f"Processing environment data for record {record_id}")

#         # 1. **Tide API Call**
#         try:
#             tide_response = requests.get(
#                 'https://example.com/tide_api',
#                 params={'timestamp': env_data.timestamp},
#                 timeout=10  # Avoid hanging requests
#             )
#             tide_response.raise_for_status()
#             tide_json = tide_response.json()
#             env_data.tide_state = tide_json.get('state')
#             env_data.tide_coefficient = tide_json.get('coefficient')
#             print(f"Tide API Success: {tide_json}")

#         except requests.exceptions.RequestException as e:
#             print(f"Tide API Error: {e}")
#             env_data.status = 'error'
#             db.session.commit()
#             return

#         # 2. **SunTime API Call**
#         try:
#             sun_api = SunTimeAPI(lat=36.72016, lng=-4.42034)
#             env_data.time_of_day = sun_api.get_time_of_day(env_data.timestamp)
#             print(f"SunTime API Success: {env_data.time_of_day}")

#         except Exception as e:
#             print(f"SunTime API Error: {e}")
#             env_data.status = 'error'
#             db.session.commit()
#             return

#         # 3. **Weather API Call**
#         try:
#             weather_api = WeatherAPI(lat=36.72016, lng=-4.42034)
#             weather_data = weather_api.get_weather_summary(env_data.timestamp, 
#                                                            lat=36.72016, 
#                                                            lng=-4.42034)
#             if weather_data:
#                 env_data.temperature_2m = float(weather_data.get("temperature_2m (°C)", 0.0))
#                 env_data.wind_speed_10m = float(weather_data.get("wind_speed_10m (km/h)", 0.0))
#                 env_data.wind_direction_10m = float(weather_data.get("wind_direction_10m (°)", 0.0))
#                 env_data.cloudcover_low = float(weather_data.get("cloudcover_low (%)", 0.0))
#                 env_data.cloudcover_mid = float(weather_data.get("cloudcover_mid (%)", 0.0))
#                 env_data.cloudcover_high = float(weather_data.get("cloudcover_high (%)", 0.0))
#                 print(f"Weather API Success: {json.dumps(weather_data, indent=2)}")

#         except requests.exceptions.RequestException as e:
#             print(f"Weather API Error: {e}")
#             env_data.status = 'error'
#             db.session.commit()
#             return

#         # 4. **Tide Cycle Fraction & Hour**
#         try:
#             with open('api_calls/tide_api_key') as f:
#                 api_key = f.read().strip()
            
#             tide_station = TideStation(api_key=api_key)
#             fraction, hours = tide_station.get_current_tide_cycle(
#                 lat=36.72016,
#                 lon=-4.42034,
#                 now_dt=env_data.timestamp
#             )
#             env_data.tide_cycle_fraction = fraction
#             env_data.tide_cycle_hour = hours
#             print(f"Tide Cycle Success: Fraction={fraction}, Hours={hours}")

#         except Exception as e:
#             print(f"Tide Cycle API Error: {e}")
#             env_data.status = 'error'
#             db.session.commit()
#             return

#         # 5. **Mark task as complete**
#         env_data.status = 'complete'
#         print(f"Task for record {record_id} completed successfully.")

#         db.session.commit()

#     except Exception as e:
#         print(f"General Task Error: {e}")
#         db.session.rollback()
#         env_data.status = 'error'
#         db.session.commit()


from celery_app import celery
from models import db, EnvironmentData
from api_calls.tide_cycle import TideStation
from api_calls.weather import WeatherAPI
from api_calls.suntimes import SunTimeAPI
import json

# Use consistent coordinates (update as needed)
LAT = 50.220564
LNG = -4.801677

@celery.task(name='fetch_env_data')
def fetch_env_data(record_id):
    """Fetch environmental data for a given timestamp."""
    env_data = EnvironmentData.query.get(record_id)
    if not env_data:
        print(f"Record ID {record_id} not found.")
        return

    try:
        print(f"Processing environment data for record {record_id}")

        # 1. SunTime API Call: get sun state
        try:
            sun_api = SunTimeAPI(lat=LAT, lng=LNG)
            sun_state = sun_api.get_time_of_day(env_data.timestamp)
            env_data.sun_state = sun_state
            print(f"SunTime API Success: {sun_state}")
        except Exception as e:
            print(f"SunTime API Error: {e}")
            env_data.status = 'error'
            db.session.commit()
            return

        # 2. Weather API Call: get weather summary
        try:
            weather_api = WeatherAPI(lat=LAT, lng=LNG)
            weather_data = weather_api.get_weather_summary(env_data.timestamp, LAT, LNG)
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

        # 3. Tide Cycle API Call: get tide cycle fraction and hour
        try:
            # Read the API key from file (ensure the file exists and is accessible)
            with open('api_calls/tide_api_key') as f:
                api_key = f.read().strip()

            tide_station = TideStation(api_key=api_key)
            fraction, hours = tide_station.get_current_tide_cycle(lat=LAT, lon=LNG, now_dt=env_data.timestamp)
            env_data.tide_cycle_fraction = fraction
            env_data.tide_cycle_hour = hours
            print(f"Tide Cycle API Success: Fraction={fraction}, Hours={hours}")
        except Exception as e:
            print(f"Tide Cycle API Error: {e}")
            env_data.status = 'error'
            db.session.commit()
            return

        # Mark the task as complete
        env_data.status = 'complete'
        print(f"Task for record {record_id} completed successfully.")
        db.session.commit()

    except Exception as e:
        print(f"General Task Error: {e}")
        db.session.rollback()
        env_data.status = 'error'
        db.session.commit()
