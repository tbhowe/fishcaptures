import requests
import numpy as np
from datetime import datetime, timedelta

class SunTimeAPI:
    BASE_URL = "https://api.sunrise-sunset.org/json"
    
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
    
    def fetch_data(self, date=None, formatted=1):
        params = {
            'lat': self.lat,
            'lng': self.lng,
            'formatted': formatted
        }
        if date:
            params['date'] = date
        
        response = requests.get(self.BASE_URL, params=params)
        return response.json()
    
    @staticmethod
    def extract_times(data):
        if data['status'] != 'OK':
            print(f"Error: {data['status']}")
            return None
        
        results = data['results']
        # We’ll return a dict for easier reference
        return {
            "sunrise": results["sunrise"],
            "sunset": results["sunset"],
            "civil_twilight_begin": results["civil_twilight_begin"],
            "civil_twilight_end": results["civil_twilight_end"],
            "nautical_twilight_begin": results["nautical_twilight_begin"],
            "nautical_twilight_end": results["nautical_twilight_end"],
            "astronomical_twilight_begin": results["astronomical_twilight_begin"],
            "astronomical_twilight_end": results["astronomical_twilight_end"],
        }

    @staticmethod
    def adjust_for_dst(date_str):
        """
        Very rough DST adjustment for UK.
        Adds 1 hour if the date is in DST period.
        """
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Last Sunday of March
        last_sunday_march = max(datetime(date_obj.year, 3, day) for day in range(25, 32) if datetime(date_obj.year, 3, day).weekday() == 6)
        # Last Sunday of October
        last_sunday_october = max(datetime(date_obj.year, 10, day) for day in range(25, 32) if datetime(date_obj.year, 10, day).weekday() == 6)

        if last_sunday_march <= date_obj < last_sunday_october:
            return timedelta(hours=1)
        return timedelta()

    def get_sun_times(self, date, formatted=1):
        """Fetch sunrise, sunset, and twilight times for a given date. Returns a dict with string times."""
        data = self.fetch_data(date, formatted)
        return self.extract_times(data)

    def parse_time(self, date_str, time_str):
        """
        Given a date string (YYYY-MM-DD) and a time string (e.g. '06:30:00 AM'),
        return a datetime object with a rough DST adjustment.
        """
        dst_adjustment = self.adjust_for_dst(date_str)
        # Convert the 'hh:mm:ss AM/PM' format into a base datetime
        base_dt = datetime.strptime(time_str, "%I:%M:%S %p")
        # Replace with the actual date but keep the time from base_dt
        date_dt = datetime.strptime(date_str, "%Y-%m-%d")
        combined_dt = datetime(
            year=date_dt.year,
            month=date_dt.month,
            day=date_dt.day,
            hour=base_dt.hour,
            minute=base_dt.minute,
            second=base_dt.second
        )
        # Apply DST offset if needed
        combined_dt += dst_adjustment
        return combined_dt

    def get_time_of_day(self, dt):
        """
        Given a datetime object, returns:
        'night', 'daylight', 'civil twilight', 'nautical twilight', or 'astronomical twilight'
        based on the sun/twilight times for that date.
        """
        date_str = dt.strftime("%Y-%m-%d")
        sun_times = self.get_sun_times(date_str)

        # If API call failed or is invalid
        if not sun_times:
            return "unknown"

        # Convert times to full datetime objects
        sunrise = self.parse_time(date_str, sun_times["sunrise"])
        sunset = self.parse_time(date_str, sun_times["sunset"])
        civil_begin = self.parse_time(date_str, sun_times["civil_twilight_begin"])
        civil_end = self.parse_time(date_str, sun_times["civil_twilight_end"])
        nautical_begin = self.parse_time(date_str, sun_times["nautical_twilight_begin"])
        nautical_end = self.parse_time(date_str, sun_times["nautical_twilight_end"])
        astro_begin = self.parse_time(date_str, sun_times["astronomical_twilight_begin"])
        astro_end = self.parse_time(date_str, sun_times["astronomical_twilight_end"])

        # Compare in ascending order
        if dt < astro_begin or dt >= astro_end:
            return "night"
        elif dt < nautical_begin:
            return "astronomical twilight"
        elif dt < civil_begin:
            return "nautical twilight"
        elif dt < sunrise:
            return "civil twilight"
        elif dt < sunset:
            return "daylight"
        elif dt < civil_end:
            return "civil twilight"
        elif dt < nautical_end:
            return "nautical twilight"
        elif dt < astro_end:
            return "astronomical twilight"
        else:
            return "night"


# Example usage:
if __name__ == "__main__":
    lat = 36.7201600
    lng = -4.4203400
    api = SunTimeAPI(lat, lng)

    # Example timestamp
    test_datetime = datetime(2023, 9, 8, 5, 0, 0)  # 2023-09-08 05:00:00
    time_of_day = api.get_time_of_day(test_datetime)
    print(f"At {test_datetime}, it's {time_of_day}.")
