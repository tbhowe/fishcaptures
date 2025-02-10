#%%
from skyfield.api import Topos, load
from datetime import datetime

def compute_declinations(ts, lat, lon, date):
    """Compute the solar and lunar declinations for a given date and location."""
    
    planets = load('de421.bsp')  # Loading planetary ephemeris data
    earth = planets['earth']
    sun = planets['sun']
    moon = planets['moon']
    
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    t = ts.utc(date.year, date.month, date.day)
    
    astrometric_sun = observer.at(t).observe(sun).apparent()
    astrometric_moon = observer.at(t).observe(moon).apparent()
    
    alt_sun, az_sun, d_sun = astrometric_sun.altaz()
    alt_moon, az_moon, d_moon = astrometric_moon.altaz()
    
    return alt_sun.degrees, alt_moon.degrees

def tidal_coefficient(lat, lon, date):
    """Compute tidal coefficient based on location and date."""
    
    ts = load.timescale()  # Loading timescale data for date calculations
    
    declination_sun, declination_moon = compute_declinations(ts, lat, lon, date)
    
    # Formula for tidal coefficient based on declinations might vary, adjust as needed
    coefficient = abs(declination_sun) + abs(declination_moon)
    
    return coefficient

if __name__ == "__main__":
    date_obj = datetime.strptime("2023-09-16", "%Y-%m-%d")
    lat, lon = 50.220564, -4.801677
    coef = tidal_coefficient(lat, lon, date_obj)
    print(f'Tidal Coefficient for {date_obj.date()}: {coef}')

# %%
