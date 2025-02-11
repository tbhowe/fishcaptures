#%%
import os
import arrow
import requests
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

class AstronomyAPIClient:
    """
    A client for fetching astronomy data from the Stormglass Astronomy API.

    This client retrieves a 24‑hour window of astronomy data (from midnight to midnight UTC)
    for a given timestamp and geographic coordinates. It then extracts a subset of fields and
    computes a single "lightLevel" indicator (one of: "Night", "Astronomical twilight", 
    "Nautical twilight", "Civil Twilight", or "Daylight") based on the twilight and 
    sunrise/sunset times.

    The API key is obtained from the environment variable STORMGLASS_API_KEY.
    """

    def __init__(self, api_key: str = None, base_url: str = "https://api.stormglass.io/v2/astronomy/point"):
        """
        Initialize the AstronomyAPIClient.

        Args:
            api_key (str, optional): The Stormglass API key. If not provided, it is read
                                     from the STORMGLASS_API_KEY environment variable.
            base_url (str, optional): The base URL for the Stormglass Astronomy API.
                                      Defaults to "https://api.stormglass.io/v2/astronomy/point".
        """
        if api_key is None:
            api_key = os.getenv("STORMGLASS_API_KEY")
        if not api_key:
            raise ValueError("API key is not set. Please set STORMGLASS_API_KEY in your environment.")
        self.api_key = api_key
        self.base_url = base_url

    def compute_light_level(self, target: datetime, data: Dict[str, Any]) -> str:
        """
        Compute a single light level value based on astronomy API data.

        The API returns various twilight and sunrise/sunset timestamps (all in UTC):
          - astronomicalDawn, nauticalDawn, civilDawn, sunrise,
          - sunset, civilDusk, nauticalDusk, astronomicalDusk.
        The logic is as follows:
          - If target is between sunrise and sunset, return "Daylight".
          - If target is before sunrise:
              * If target >= civilDawn, return "Civil Twilight".
              * Else if target >= nauticalDawn, return "Nautical twilight".
              * Else if target >= astronomicalDawn, return "Astronomical twilight".
              * Else return "Night".
          - If target is after sunset:
              * If target < civilDusk, return "Civil Twilight".
              * Else if target < nauticalDusk, return "Nautical twilight".
              * Else if target < astronomicalDusk, return "Astronomical twilight".
              * Else return "Night".
        If critical thresholds (sunrise, sunset, astronomicalDawn, astronomicalDusk) are missing,
        it defaults to "Night".

        Args:
            target (datetime): The target time (in UTC) to evaluate.
            data (dict): One data entry from the API response containing the relevant timestamps.

        Returns:
            str: One of "Night", "Astronomical twilight", "Nautical twilight", "Civil Twilight", or "Daylight".
        """
        def parse_time(key: str) -> Any:
            val = data.get(key)
            if val:
                try:
                    return arrow.get(val).datetime
                except Exception:
                    return None
            return None

        astronomicalDawn = parse_time("astronomicalDawn")
        nauticalDawn     = parse_time("nauticalDawn")
        civilDawn        = parse_time("civilDawn")
        sunrise          = parse_time("sunrise")
        sunset           = parse_time("sunset")
        civilDusk        = parse_time("civilDusk")
        nauticalDusk     = parse_time("nauticalDusk")
        astronomicalDusk = parse_time("astronomicalDusk")

        if sunrise is None or sunset is None or astronomicalDawn is None or astronomicalDusk is None:
            return "Night"

        if sunrise <= target < sunset:
            return "Daylight"

        if target < sunrise:
            if civilDawn is not None and target >= civilDawn:
                return "Civil Twilight"
            elif nauticalDawn is not None and target >= nauticalDawn:
                return "Nautical twilight"
            elif astronomicalDawn is not None and target >= astronomicalDawn:
                return "Astronomical twilight"
            else:
                return "Night"

        if target >= sunset:
            if civilDusk is not None and target < civilDusk:
                return "Civil Twilight"
            elif nauticalDusk is not None and target < nauticalDusk:
                return "Nautical twilight"
            elif astronomicalDusk is not None and target < astronomicalDusk:
                return "Astronomical twilight"
            else:
                return "Night"

        return "Night"

    def get_astronomy_data(self, timestamp: datetime, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch astronomy data for a given timestamp and geographic coordinates.

        This method:
          1. Defines a 24‑hour window (from midnight to midnight UTC) for the query.
          2. Sends a GET request to the Stormglass Astronomy API.
          3. Uses the first data entry from the returned data.
          4. Extracts a subset of fields: sunrise, sunset, moonrise, moonset, moonFraction,
             currentMoonPhaseText, currentMoonPhaseValue.
          5. Computes a single "lightLevel" value using compute_light_level().
          6. Returns a dictionary with all the above data.

        Args:
            timestamp (datetime): The timestamp for which astronomy data is desired.
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.

        Returns:
            dict: A dictionary containing the astronomy data and a "lightLevel" key.
        """
        start = arrow.get(timestamp).floor('day')
        end = arrow.get(timestamp).shift(days=1).floor('day')

        response = requests.get(
            self.base_url,
            params={
                'lat': lat,
                'lng': lon,
                'start': start.to('UTC').timestamp(),
                'end': end.to('UTC').timestamp()
            },
            headers={
                'Authorization': self.api_key
            }
        )
        response.raise_for_status()
        json_data = response.json()

        if "data" not in json_data or not json_data["data"]:
            return {}

        data_entry = json_data["data"][0]
        target = arrow.get(timestamp).datetime

        result = {
            "sunrise": data_entry.get("sunrise"),
            "sunset": data_entry.get("sunset"),
            "moonrise": data_entry.get("moonrise"),
            "moonset": data_entry.get("moonset"),
            "moonFraction": data_entry.get("moonFraction")
        }

        moon_phase = data_entry.get("moonPhase", {})
        current_phase = moon_phase.get("current", {})
        result["currentMoonPhaseText"] = current_phase.get("text")
        result["currentMoonPhaseValue"] = current_phase.get("value")

        result["lightLevel"] = self.compute_light_level(target, data_entry)

        return result

if __name__ == "__main__":
    from datetime import datetime
    test_date = datetime.strptime("2023-09-16", "%Y-%m-%d")
    lat, lon = 50.220564, -4.801677
    client = AstronomyAPIClient()
    data = client.get_astronomy_data(test_date, lat, lon)
    print("Astronomy data:", data)

# %%
