#%%
import os
import arrow
import requests
import math
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class WeatherAPIClient:
    """
    A client for fetching weather data from the Stormglass API.
    
    This class queries the Stormglass endpoint for a full day of weather data based
    on a given timestamp and geographic coordinates. It then selects the hourly data
    point closest to the provided timestamp and returns a subset of weather parameters.
    
    Attributes:
        api_key (str): The API key used for authorization with the Stormglass API.
        base_url (str): The base URL for the Stormglass weather endpoint.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.stormglass.io/v2/weather/point"):
        """
        Initialize the WeatherAPIClient.
        
        If no API key is provided, the client will attempt to read STORMGLASS_API_KEY
        from the environment variables.
        
        Args:
            api_key (str, optional): Your Stormglass API key. If not provided, it is
                                     read from the environment.
            base_url (str, optional): The Stormglass weather endpoint URL.
                                      Defaults to "https://api.stormglass.io/v2/weather/point".
        """
        if api_key is None:
            api_key = os.getenv("STORMGLASS_API_KEY")
        if not api_key:
            raise ValueError("API key is not set. Please set STORMGLASS_API_KEY in your environment.")
        self.api_key = api_key
        self.base_url = base_url

    def _select_value(self, data: Dict) -> Optional[float]:
        """
        Select a numerical value from a provider data dictionary.
        
        Preference is given to the 'noaa' provider if available.
        
        Args:
            data (dict): A dictionary mapping provider names to their reported values.
            
        Returns:
            Optional[float]: The chosen value as a float, or None if no valid value is found.
        """
        if "noaa" in data:
            try:
                return float(data["noaa"])
            except (ValueError, TypeError):
                pass
        for provider, value in data.items():
            try:
                return float(value)
            except (ValueError, TypeError):
                continue
        return None

    def get_weather_data(self, timestamp: datetime, lat: float, lon: float) -> Dict:
        """
        Fetch weather data for a given timestamp and geographic coordinates.
        
        This method:
          1. Determines the start and end times (full day) using Arrow.
          2. Sends a GET request to the Stormglass API with the desired parameters.
          3. Finds the hourly data entry closest in time to the provided timestamp.
          4. Extracts and returns a subset of weather parameters.
        
        Desired parameters include air temperature, pressure, cloud cover, current and swell data,
        wave data, wind direction/speed, gust, etc.
        
        Args:
            timestamp (datetime): The timestamp for which weather data is desired.
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
        
        Returns:
            dict: A dictionary containing the selected weather parameters and their values.
        """
        start = arrow.get(timestamp).floor('day')
        end = arrow.get(timestamp).ceil('day')
        
        params_list = [
            "airTemperature", "pressure", "cloudCover", "currentDirection", "currentSpeed",
            "swellDirection", "swellHeight", "swellPeriod", "secondarySwellPeriod", "secondarySwellDirection",
            "secondarySwellHeight", "waveDirection", "waveHeight", "wavePeriod",
            "windWaveDirection", "windWaveHeight", "windWavePeriod",
            "windDirection", "windSpeed", "gust"
        ]
        
        params_str = ",".join(params_list)
        
        response = requests.get(
            self.base_url,
            params={
                'lat': lat,
                'lng': lon,
                'params': params_str,
                'start': start.to('UTC').timestamp(),
                'end': end.to('UTC').timestamp()
            },
            headers={
                'Authorization': self.api_key
            }
        )
        
        response.raise_for_status()
        json_data = response.json()
        
        target = arrow.get(timestamp)
        closest_hour = None
        min_diff = None
        for hour in json_data.get("hours", []):
            hour_time = arrow.get(hour["time"])
            diff = abs((hour_time - target).total_seconds())
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_hour = hour
        
        if closest_hour is None:
            return {}
        
        result = {}
        for key in params_list:
            if key in closest_hour:
                result[key] = self._select_value(closest_hour[key])
            else:
                result[key] = None
        
        return result

if __name__ == "__main__":
    # Example usage:
    test_date = datetime.strptime("2023-09-16", "%Y-%m-%d")
    lat, lon = 50.220564, -4.801677
    client = WeatherAPIClient()  # Reads API key from environment.
    weather = client.get_weather_data(test_date, lat, lon)
    print("Weather data:", weather)
