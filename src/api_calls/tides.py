#%%
import os
import arrow
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

class TideAPIClient:
    """
    A client for fetching tide data from the Stormglass API.

    This client uses two endpoints:
      - The Extremes Point Request endpoint to retrieve tide extremes (high and low tide events).
      - The Sea Level Point Request endpoint to retrieve hourly sea level data.

    It computes two values:
      - currentTideHeight: The sea level (relative to the chosen datum) at the target time,
         selected from the sea-level data.
      - tideHour: The hours elapsed since the most recent high tide. If the target time is before the first
         high tide of the day, the previous day's extremes are queried.

    In addition, it now returns the following extreme values for the day:
      - maxHighTide: The highest tide height (for high tide events).
      - minLowTide: The lowest tide height (for low tide events).

    The API key is read from the environment variable STORMGLASS_API_KEY.
    """

    def __init__(self, 
                 api_key: str = None, 
                 datum: str = "MSL", 
                 base_url_extremes: str = "https://api.stormglass.io/v2/tide/extremes/point",
                 base_url_sea_level: str = "https://api.stormglass.io/v2/tide/sea-level/point"):
        """
        Initialize the TideAPIClient.

        Args:
            api_key (str, optional): Your Stormglass API key. If not provided, it is read from the environment.
            datum (str, optional): The datum to use (e.g., "MSL" or "MLLW"). Defaults to "MSL".
            base_url_extremes (str, optional): URL for the extremes endpoint.
            base_url_sea_level (str, optional): URL for the sea-level endpoint.
        """
        if api_key is None:
            api_key = os.getenv("STORMGLASS_API_KEY")
        if not api_key:
            raise ValueError("API key is not set. Please set STORMGLASS_API_KEY in your environment.")
        self.api_key = api_key
        self.datum = datum
        self.base_url_extremes = base_url_extremes
        self.base_url_sea_level = base_url_sea_level

    def _query_extremes(self, start: arrow.Arrow, end: arrow.Arrow, lat: float, lon: float) -> List[Dict[str, Any]]:
        """
        Query the extremes endpoint for the given period.

        Args:
            start (arrow.Arrow): Start of the query period.
            end (arrow.Arrow): End of the query period.
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            List[dict]: List of extreme tide events.
        """
        params = {
            'lat': lat,
            'lng': lon,
            'start': start.to('UTC').timestamp(),
            'end': end.to('UTC').timestamp(),
            'datum': self.datum
        }
        response = requests.get(self.base_url_extremes, params=params,
                                headers={'Authorization': self.api_key})
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("data", [])

    def _query_sea_level(self, start: arrow.Arrow, end: arrow.Arrow, lat: float, lon: float) -> List[Dict[str, Any]]:
        """
        Query the sea-level endpoint for the given period.

        Args:
            start (arrow.Arrow): Start of the query period.
            end (arrow.Arrow): End of the query period.
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            List[dict]: List of sea level data points.
        """
        params = {
            'lat': lat,
            'lng': lon,
            'start': start.to('UTC').timestamp(),
            'end': end.to('UTC').timestamp(),
            'datum': self.datum
        }
        response = requests.get(self.base_url_sea_level, params=params,
                                headers={'Authorization': self.api_key})
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("data", [])

    def _get_most_recent_high_tide(self, target: datetime, extremes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the most recent high tide event (type "high") with time ≤ target.

        Args:
            target (datetime): The target time (UTC). If naive, assumed UTC.
            extremes (List[dict]): List of tide extreme events.

        Returns:
            dict or None: The high tide event, or None if not found.
        """
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        recent_high = None
        for event in extremes:
            if event.get("type") == "high":
                event_time = arrow.get(event["time"]).datetime
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=timezone.utc)
                if event_time <= target:
                    if recent_high is None or arrow.get(recent_high["time"]).datetime < event_time:
                        recent_high = event
        return recent_high

    def _get_tidal_range(self, extremes: List[Dict[str, Any]]) -> Optional[float]:
        """
        Compute the tidal range from the extremes data as (max high tide – min low tide).

        Args:
            extremes (List[dict]): List of tide extreme events.

        Returns:
            float or None: The tidal range, or None if data is insufficient.
        """
        high_tides = [float(event["height"]) for event in extremes if event.get("type") == "high"]
        low_tides = [float(event["height"]) for event in extremes if event.get("type") == "low"]
        if not high_tides or not low_tides:
            return None
        return max(high_tides) - min(low_tides)

    def get_tide_data(self, timestamp: datetime, lat: float, lon: float) -> Dict[str, Any]:
        """
        Retrieve tide data for a given timestamp and location. Computes:
          - currentTideHeight: Sea level value (from hourly data) closest to the target time.
          - tideHour: Hours elapsed since the most recent high tide.
                      If no high tide is found in the current day, the previous day's extremes are queried.
          - maxHighTide: The highest tide height (maximum of high tide events) for the day.
          - minLowTide: The lowest tide height (minimum of low tide events) for the day.
        
        Args:
            timestamp (datetime): The target time (UTC). If naive, assumed UTC.
            lat (float): Latitude.
            lon (float): Longitude.
        
        Returns:
            dict: A dictionary with keys "currentTideHeight", "tideHour", "maxHighTide", and "minLowTide".
        """
        start = arrow.get(timestamp).floor('day')
        end = arrow.get(timestamp).shift(days=1).floor('day')
        extremes = self._query_extremes(start, end, lat, lon)
        sea_levels = self._query_sea_level(start, end, lat, lon)

        # 1. currentTideHeight: find the sea level data point closest to target time.
        current_tide_height = None
        if sea_levels:
            target_arrow = arrow.get(timestamp)
            closest_point = min(sea_levels, key=lambda point: abs(arrow.get(point["time"]) - target_arrow))
            current_tide_height = closest_point.get("sg")
            if current_tide_height is not None:
                current_tide_height = float(current_tide_height)

        # 2. tideHour: compute hours since the most recent high tide.
        target_dt = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        recent_high = self._get_most_recent_high_tide(target_dt, extremes)
        if recent_high is None:
            # Query previous day if no high tide is found in current day.
            prev_start = start.shift(days=-1)
            prev_end = start
            prev_extremes = self._query_extremes(prev_start, prev_end, lat, lon)
            recent_high = self._get_most_recent_high_tide(target_dt, prev_extremes)
        tide_hour = None
        if recent_high:
            high_time = arrow.get(recent_high["time"]).datetime
            if high_time.tzinfo is None:
                high_time = high_time.replace(tzinfo=timezone.utc)
            diff = (target_dt - high_time).total_seconds() / 3600.0
            tide_hour = max(0, min(diff, 12))  # Clamp between 0 and 12

        # 3. maxHighTide and minLowTide: from extremes data.
        max_high_tide = None
        min_low_tide = None
        high_values = [float(event["height"]) for event in extremes if event.get("type") == "high"]
        low_values = [float(event["height"]) for event in extremes if event.get("type") == "low"]
        if high_values:
            max_high_tide = max(high_values)
        if low_values:
            min_low_tide = min(low_values)

        return {
            "currentTideHeight": current_tide_height,
            "tideHour": tide_hour,
            "maxHighTide": max_high_tide,
            "minLowTide": min_low_tide
        }

if __name__ == "__main__":
    from datetime import datetime
    # Example usage with a fixed date.
    test_date = datetime.strptime("2023-09-16", "%Y-%m-%d")
    lat, lon = 60.936, 5.114  # Example coordinates
    client = TideAPIClient()
    tide_data = client.get_tide_data(test_date, lat, lon)
    print("Tide data:", tide_data)

# %%
