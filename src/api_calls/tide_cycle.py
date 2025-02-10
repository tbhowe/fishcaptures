# #%%
# import requests
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta, timezone

# class TideStation:
#     BASE_URL = 'https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations'

#     def __init__(self, api_key):
#         self.api_key = api_key
#         self.headers = {'Ocp-Apim-Subscription-Key': self.api_key}
#         self.df_stations = self._get_tide_stations_dataframe()
    
#     @staticmethod
#     def parse_as_utc(dt_str: str) -> datetime:
#         dt = datetime.fromisoformat(dt_str)
#         # If no timezone is present in the string, make it UTC.
#         if dt.tzinfo is None:
#             dt = dt.replace(tzinfo=timezone.utc)
#         return dt

#     def _get_tide_stations_dataframe(self):
#         # Retrieve station data (GeoJSON-like format)
#         try:
#             response = requests.get(self.BASE_URL, headers=self.headers)
#             response.raise_for_status()
#             data = response.json()

#             rows = [
#                 [
#                     feature['geometry']['coordinates'][1],  # latitude
#                     feature['geometry']['coordinates'][0],  # longitude
#                     feature['properties']['Name'],
#                     feature['properties']['Id'],
#                     feature['properties']['ContinuousHeightsAvailable']
#                 ]
#                 for feature in data['features']
#             ]

#             return pd.DataFrame(rows, columns=['Latitude', 'Longitude', 'Name', 'id', 'ContinuousHeightsAvailable'])
#         except requests.exceptions.RequestException as e:
#             print(f"Error retrieving stations: {e}")
#             return pd.DataFrame([])

#     @staticmethod
#     def _haversine(lat1, lon1, lat2, lon2):
#         R = 6371.0  # Earth radius in km
#         lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1
#         a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
#         c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
#         return R * c

#     def closest_station(self, lat, lon):
#         if self.df_stations.empty:
#             return None

#         # Calculate distances for each station
#         self.df_stations['distance'] = self._haversine(
#             lat, lon,
#             self.df_stations['Latitude'],
#             self.df_stations['Longitude']
#         )
#         # Filter to only stations with ContinuousHeightsAvailable == True
#         valid_stations = self.df_stations[self.df_stations['ContinuousHeightsAvailable'] == True]
#         if valid_stations.empty:
#             return None

#         # Return the single closest station
#         closest = valid_stations.nsmallest(1, 'distance')
#         return closest.iloc[0]

#     def get_tide_data(self, station_id: str, days: int = 2):
#         """
#         Retrieves tidal events for the given station, for the specified number of days.
#         duration=2 => ~48 hours of data
#         """
#         endpoint = f'{self.BASE_URL}/{station_id}/TidalEvents?duration={days}'
#         response = requests.get(endpoint, headers=self.headers)
#         response.raise_for_status()
#         return response.json()

#     @staticmethod
#     def tide_cycle_fraction(now_dt: datetime, tide_data: list) -> float:
#         """
#         Returns a fraction of where we are in the tide cycle:
#           0.0 => just hit a HighWater (T1)
#           0.5 => just hit the next LowWater (T2)
#           1.0 => about to hit the next HighWater (T3)

#         Using the pattern: T1 (most recent HighWater <= now)
#                            T2 (next LowWater after T1)
#                            T3 (next HighWater after T2)
#         """
#         # Sort events by time
#         events = sorted(tide_data, key=lambda x: TideStation.parse_as_utc(x['DateTime']))

#         # 1) Find the LAST HighWater <= now => T1
#         T1_idx = None
#         for i, e in enumerate(events):
#             if e['EventType'] == 'HighWater':
#                 event_time = TideStation.parse_as_utc(e['DateTime'])
#                 if event_time <= now_dt:
#                     T1_idx = i

#         # If none found, use first future HighWater
#         if T1_idx is None:
#             for i, e in enumerate(events):
#                 if e['EventType'] == 'HighWater':
#                     event_time = TideStation.parse_as_utc(e['DateTime'])
#                     if event_time >= now_dt:
#                         T1_idx = i
#                         break
#             if T1_idx is None:
#                 return 0.0  # No HighWater at all

#         T1_time = TideStation.parse_as_utc(events[T1_idx]['DateTime'])

#         # 2) Next LowWater => T2
#         T2_idx = None
#         for j in range(T1_idx + 1, len(events)):
#             if events[j]['EventType'] == 'LowWater':
#                 T2_idx = j
#                 break
#         if T2_idx is None:
#             return 0.0
#         T2_time = TideStation.parse_as_utc(events[T2_idx]['DateTime'])

#         # 3) Next HighWater => T3
#         T3_idx = None
#         for k in range(T2_idx + 1, len(events)):
#             if events[k]['EventType'] == 'HighWater':
#                 T3_idx = k
#                 break
#         if T3_idx is None:
#             return 0.0
#         T3_time = TideStation.parse_as_utc(events[T3_idx]['DateTime'])

#         # If now is after T3, clamp to 1.0
#         if now_dt >= T3_time:
#             return 1.0

#         # If now is before T1_time, do the "previous cycle" guess
#         if now_dt < T1_time:
#             # Guess T0 time by going backwards from T1_time
#             half_cycle_len = (T3_time - T2_time)  # approximate
#             T0_time = T1_time - half_cycle_len
#             if now_dt < T0_time:
#                 return 0.0
#             total_secs = (T1_time - T0_time).total_seconds()
#             elapsed = (now_dt - T0_time).total_seconds()
#             return max(0.0, min(elapsed / total_secs, 1.0))

#         # Otherwise, we know T1_time <= now_dt < T3_time
#         if T1_time <= now_dt < T2_time:
#             # T1->T2 => fraction 0.0 -> 0.5
#             total_secs = (T2_time - T1_time).total_seconds()
#             elapsed = (now_dt - T1_time).total_seconds()
#             frac = 0.5 * (elapsed / total_secs)
#             return max(0.0, min(frac, 0.5))
#         else:
#             # T2->T3 => fraction 0.5 -> 1.0
#             total_secs = (T3_time - T2_time).total_seconds()
#             elapsed = (now_dt - T2_time).total_seconds()
#             frac = 0.5 + 0.5 * (elapsed / total_secs)
#             return max(0.5, min(frac, 1.0))

#     def get_current_tide_cycle(self, lat: float, lon: float, now_dt: datetime = None):
#         """
#         Returns (fraction, hours) of the current tide cycle for the given lat/lon.
#           fraction: a value in [0..1]
#           hours: fraction * 12

#         Example usage:
#           fraction, hours = obj.get_current_tide_cycle(50.220564, -4.801677)
#         """
#         if now_dt is None:
#             now_dt = datetime.now(timezone.utc)

#         # Find the nearest station
#         station_row = self.closest_station(lat, lon)
#         if station_row is None:
#             print("No suitable station found.")
#             return 0.0, 0.0

#         station_id = station_row['id']
#         # Retrieve ~48 hours of data
#         tide_data = self.get_tide_data(station_id, days=2)

#         fraction = self.tide_cycle_fraction(now_dt, tide_data)
#         return fraction, fraction * 12

# if __name__ == '__main__':
#     from datetime import datetime, timezone

#     with open('tide_api_key') as f:
#         API_KEY = f.read().strip()

#     ts = TideStation(API_KEY)
#     # Your desired lat/lon
#     lat, lon = 50.220564, -4.801677

#     # Optional: pass a specific datetime for testing. Otherwise uses now in UTC.
#     # current_dt = datetime(2025, 2, 9, 20, 2, tzinfo=timezone.utc)
#     # fraction, hours = ts.get_current_tide_cycle(lat, lon, current_dt)

#     fraction, hours = ts.get_current_tide_cycle(lat, lon)
#     print(f"Tide cycle fraction: {fraction:.2f}")
#     print(f"Tide cycle in hours (0–12): {hours:.2f}")

# %%
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UK_TZ = ZoneInfo("Europe/London")

class TideStation:
    BASE_URL = 'https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations'

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'Ocp-Apim-Subscription-Key': self.api_key}
        self.df_stations = self._get_tide_stations_dataframe()
    
    @staticmethod
    def parse_as_utc(dt_str: str) -> datetime:
        """
        Parse the provided datetime string. The tide API always returns times in UTC.
        Convert the resulting datetime to UK local time to handle GMT/BST.
        """
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Convert UTC to UK local time (handles DST automatically)
        dt = dt.astimezone(UK_TZ)
        return dt

    def _get_tide_stations_dataframe(self):
        # Retrieve station data (GeoJSON-like format)
        try:
            response = requests.get(self.BASE_URL, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            rows = [
                [
                    feature['geometry']['coordinates'][1],  # latitude
                    feature['geometry']['coordinates'][0],  # longitude
                    feature['properties']['Name'],
                    feature['properties']['Id'],
                    feature['properties']['ContinuousHeightsAvailable']
                ]
                for feature in data['features']
            ]

            return pd.DataFrame(rows, columns=['Latitude', 'Longitude', 'Name', 'id', 'ContinuousHeightsAvailable'])
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving stations: {e}")
            return pd.DataFrame([])

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371.0  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    def closest_station(self, lat, lon):
        if self.df_stations.empty:
            return None

        # Calculate distances for each station
        self.df_stations['distance'] = self._haversine(
            lat, lon,
            self.df_stations['Latitude'],
            self.df_stations['Longitude']
        )
        # Filter to only stations with ContinuousHeightsAvailable == True
        valid_stations = self.df_stations[self.df_stations['ContinuousHeightsAvailable'] == True]
        if valid_stations.empty:
            return None

        # Return the single closest station
        closest = valid_stations.nsmallest(1, 'distance')
        return closest.iloc[0]

    def get_tide_data(self, station_id: str, days: int = 2):
        """
        Retrieves tidal events for the given station, for the specified number of days.
        duration=2 => ~48 hours of data
        """
        endpoint = f'{self.BASE_URL}/{station_id}/TidalEvents?duration={days}'
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def tide_cycle_fraction(now_dt: datetime, tide_data: list) -> float:
        """
        Returns a fraction of where we are in the tide cycle:
          0.0 => just hit a HighWater (T1)
          0.5 => just hit the next LowWater (T2)
          1.0 => about to hit the next HighWater (T3)
        
        Using the pattern: T1 (most recent HighWater <= now)
                           T2 (next LowWater after T1)
                           T3 (next HighWater after T2)
        """
        # Sort events by time (all in UK local time now)
        events = sorted(tide_data, key=lambda x: TideStation.parse_as_utc(x['DateTime']))

        # 1) Find the LAST HighWater <= now => T1
        T1_idx = None
        for i, e in enumerate(events):
            if e['EventType'] == 'HighWater':
                event_time = TideStation.parse_as_utc(e['DateTime'])
                if event_time <= now_dt:
                    T1_idx = i

        # If none found, use first future HighWater
        if T1_idx is None:
            for i, e in enumerate(events):
                if e['EventType'] == 'HighWater':
                    event_time = TideStation.parse_as_utc(e['DateTime'])
                    if event_time >= now_dt:
                        T1_idx = i
                        break
            if T1_idx is None:
                return 0.0  # No HighWater at all

        T1_time = TideStation.parse_as_utc(events[T1_idx]['DateTime'])

        # 2) Next LowWater => T2
        T2_idx = None
        for j in range(T1_idx + 1, len(events)):
            if events[j]['EventType'] == 'LowWater':
                T2_idx = j
                break
        if T2_idx is None:
            return 0.0
        T2_time = TideStation.parse_as_utc(events[T2_idx]['DateTime'])

        # 3) Next HighWater => T3
        T3_idx = None
        for k in range(T2_idx + 1, len(events)):
            if events[k]['EventType'] == 'HighWater':
                T3_idx = k
                break
        if T3_idx is None:
            return 0.0
        T3_time = TideStation.parse_as_utc(events[T3_idx]['DateTime'])

        # If now is after T3, clamp to 1.0
        if now_dt >= T3_time:
            return 1.0

        # If now is before T1_time, do the "previous cycle" guess
        if now_dt < T1_time:
            half_cycle_len = (T3_time - T2_time)  # approximate half cycle length
            T0_time = T1_time - half_cycle_len
            if now_dt < T0_time:
                return 0.0
            total_secs = (T1_time - T0_time).total_seconds()
            elapsed = (now_dt - T0_time).total_seconds()
            return max(0.0, min(elapsed / total_secs, 1.0))

        # Otherwise, we know T1_time <= now_dt < T3_time
        if T1_time <= now_dt < T2_time:
            # T1 -> T2: fraction 0.0 -> 0.5
            total_secs = (T2_time - T1_time).total_seconds()
            elapsed = (now_dt - T1_time).total_seconds()
            frac = 0.5 * (elapsed / total_secs)
            return max(0.0, min(frac, 0.5))
        else:
            # T2 -> T3: fraction 0.5 -> 1.0
            total_secs = (T3_time - T2_time).total_seconds()
            elapsed = (now_dt - T2_time).total_seconds()
            frac = 0.5 + 0.5 * (elapsed / total_secs)
            return max(0.5, min(frac, 1.0))

    def get_current_tide_cycle(self, lat: float, lon: float, now_dt: datetime = None):
        """
        Returns (fraction, hours) of the current tide cycle for the given lat/lon.
          fraction: a value in [0..1]
          hours: fraction * 12

        The tide API always returns UTC timestamps. We convert those to UK local time
        and ensure the provided now_dt is also in UK local time.
        """
        if now_dt is None:
            now_dt = datetime.now(timezone.utc).astimezone(UK_TZ)
        elif now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc).astimezone(UK_TZ)
        else:
            now_dt = now_dt.astimezone(UK_TZ)

        # Find the nearest station
        station_row = self.closest_station(lat, lon)
        if station_row is None:
            print("No suitable station found.")
            return 0.0, 0.0

        station_id = station_row['id']
        # Retrieve ~48 hours of data
        tide_data = self.get_tide_data(station_id, days=2)

        fraction = self.tide_cycle_fraction(now_dt, tide_data)
        return fraction, fraction * 12

if __name__ == '__main__':
    with open('tide_api_key') as f:
        API_KEY = f.read().strip()

    ts = TideStation(API_KEY)
    # Your desired lat/lon
    lat, lon = 50.220564, -4.801677

    # You can pass a specific datetime for testing; otherwise, uses current time in UK local time.
    fraction, hours = ts.get_current_tide_cycle(lat, lon)
    print(f"Tide cycle fraction: {fraction:.2f}")
    print(f"Tide cycle in hours (0–12): {hours:.2f}")
