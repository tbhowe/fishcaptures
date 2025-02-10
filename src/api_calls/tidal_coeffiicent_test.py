# api_calls/tidal_coefficient.py
from skyfield.api import Topos, load
from datetime import datetime

class TidalCoefficient:
    def __init__(self):
        # Preload ephemeris data and timescale for reuse.
        self.planets = load('de421.bsp')
        self.earth = self.planets['earth']
        self.sun = self.planets['sun']
        self.moon = self.planets['moon']
        self.timescale = load.timescale()

    def compute_declinations(self, lat, lon, date):
        """Compute the solar and lunar altitudes (used here as a proxy for declination) for a given date and location."""
        observer = self.earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
        t = self.timescale.utc(date.year, date.month, date.day)
        astrometric_sun = observer.at(t).observe(self.sun).apparent()
        astrometric_moon = observer.at(t).observe(self.moon).apparent()
        alt_sun, _, _ = astrometric_sun.altaz()
        alt_moon, _, _ = astrometric_moon.altaz()
        return alt_sun.degrees, alt_moon.degrees

    def get_tidal_coefficient(self, lat, lon, date):
        """
        Compute tidal coefficient based on location and date.
        For our purposes, we use a simple formula:
           tidal_coefficient = |declination_sun| + |declination_moon|
        """
        declination_sun, declination_moon = self.compute_declinations(lat, lon, date)
        coefficient = abs(declination_sun) + abs(declination_moon)
        return coefficient
