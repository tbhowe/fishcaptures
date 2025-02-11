import requests

# Coordinates for the location (example: Plymouth, UK)
lat = 50.3763
lon = -4.1438

# Your WorldTides API key (sign up at worldtides.info to get a key)
api_key = "YOUR_API_KEY"

# Prepare API request URL for one day of tide extremes and datum info
url = (
    f"https://www.worldtides.info/api/v3?"
    f"extremes&datums&date=2025-02-12&days=1"    # request tide extremes for the date (YYYY-MM-DD) and 1 day range
    f"&lat={lat}&lon={lon}&key={api_key}"
)

response = requests.get(url)
data = response.json()

# Extract HAT and LAT from the returned datums
datums_list = data.get("datums", [])
# Convert list of datums to a dict for easy lookup
datums = {d["name"]: d["height"] for d in datums_list}
hat_height = datums.get("HAT")
lat_height = datums.get("LAT")

# Compute HAT - LAT (maximum tidal range at this location)
if hat_height is not None and lat_height is not None:
    max_range = hat_height - lat_height
else:
    raise ValueError("HAT or LAT not found in datum data.")

# Extract the daily high and low tide heights from the extremes data
extremes_list = data.get("extremes", [])
if not extremes_list:
    raise ValueError("No tide extremes data returned for this location/date.")

# Find the minimum (low tide) and maximum (high tide) water levels in the extremes
low_tide_level = min(e["height"] for e in extremes_list)
high_tide_level = max(e["height"] for e in extremes_list)
daily_range = high_tide_level - low_tide_level

# Calculate the tidal coefficient as a percentage
tidal_coefficient = (daily_range / max_range) * 100

# Output the results
print(f"Location: lat={lat}, lon={lon}")
print(f"HAT: {hat_height:.2f} m, LAT: {lat_height:.2f} m")
print(f"Daily Tidal Range: {daily_range:.2f} m")
print(f"Tidal Coefficient: {tidal_coefficient:.1f}%")
