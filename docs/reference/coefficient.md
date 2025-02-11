# Implementation Instructions for Tide Coeff (for a future version)

## Retrieving HAT/LAT and Calculating Tidal Coefficient for UK Locations

**Highest Astronomical Tide (HAT)** and **Lowest Astronomical Tide (LAT)** are the extreme high and low tide levels expected under average meteorological conditions over the 18.6-year lunar cycle ([Definitions of tidal levels and other parameters | National Tidal and Sea Level Facility](https://ntslf.org/tides/definitions#:~:text=Highest%20astronomical%20tide%20,over%20a%20number%20of%20years)). To compute a **tidal coefficient** for a given day at a UK coastal location, we need: 

- **Daily tidal range** – the difference between that day’s highest and lowest tide.
- **Maximum tidal range (HAT − LAT)** – the largest possible range at that location (difference between HAT and LAT).

The tidal coefficient is then calculated as: 

\[ 
\text{tidalCoefficient} = \frac{\text{daily tidal range}}{\text{HAT} - \text{LAT}} \times 100 
\] 

This expresses the day’s tide range as a percentage of the theoretical maximum. In other words, a tidal coefficient near 100 means the tide range is close to the largest it can ever be (a spring tide near the HAT/LAT extremes), while lower values indicate a smaller range (neap tides). Some conventions (e.g. French tide tables) use a 20–120 scale for tidal coefficients ([Brest Tidal Coefficient | YBW Forum](https://forums.ybw.com/threads/brest-tidal-coefficient.114265/#:~:text=James%2C)), but the above formula yields a 0–100% scale where 100 corresponds to the HAT-LAT range.

## Public APIs for UK Tide Data (Including HAT and LAT)

Finding a public API that provides HAT and LAT for a given latitude/longitude in the UK is crucial since not all tide APIs include these datums. For example, the Stormglass API offers predicted tide heights and timing of high/low tides, but **does not provide HAT or LAT values** in its responses (it lacks tidal datum information). We need an API that includes tidal datum reference levels.

Two suitable options that cover UK waters are:

- **Admiralty UK Tidal API (UK Hydrographic Office)** – The UKHO’s official API provides authoritative tidal predictions for ~607 standard and secondary ports around the UK ([UK Tidal API - Discovery - API Catalogue](https://www.api.gov.uk/ukho/uk-tidal-api-discovery/#:~:text=The%20ADMIRALTY%20UK%20Tidal%20API,stations%20around%20the%20United%20Kingdom)). Developers can retrieve high/low tide times and heights for the current day and up to 6 days ahead on the free “Discovery” tier. However, **HAT/LAT are not directly returned** in the basic predictions; they are considered reference levels determined over the 19-year cycle. In principle, one could derive HAT/LAT by analyzing a long period of predictions (or use published Admiralty Tide Tables). The Admiralty API is reliable for UK locations, but accessing HAT/LAT may require additional steps or the premium service. (The UKHO notes that HAT values for standard ports are published in tide tables and require long-term analysis ([ADMIRALTY EasyTide](https://easytide.admiralty.co.uk/FAQs#:~:text=A%3AAnswer%20Values%20of%20HAT%20can,in%20Table%20V%2C%20Part%202)) ([ADMIRALTY EasyTide](https://easytide.admiralty.co.uk/FAQs#:~:text=In%20addition%2C%20our%20commercial%20tidal,Service%20website%20for%20more%20information)).)

- **WorldTides API (worldtides.info)** – A global tide API that covers any coordinate (including UK coasts) and **explicitly provides tidal datums such as HAT and LAT**. You can query by latitude/longitude and request tide predictions *and* datum information. The API returns an array of vertical datums (e.g. HAT, LAT, Mean Sea Level, etc.) for the location ([WorldTides - Datums](https://www.worldtides.info/datums#:~:text=MHHWS%20Mean%20Higher%20High%20Water,The%20highest%20predicted%20astronomical%20tide)). For example, including the `datums` parameter in the request yields values for HAT and LAT (among others) for that coordinate. This API also returns tide **extremes** (high and low water events) which we can use to find the daily range. An example request might include `&datums&extremes` for a given `lat, lon` ([WorldTides - Apidocs](https://www.worldtides.info/apidocs#:~:text=Get%20the%20tidal%20extremes%20referenced,and%20the%20datums)). The WorldTides API requires a free API key (with a limited daily quota of requests), but it is publicly accessible and well-documented.

Given the need for HAT/LAT specifically, the **WorldTides API is a convenient choice**. It provides both the daily tide data and the datum information in one call, making it straightforward to compute the tidal coefficient. (Other sources like the UK Environment Agency’s tide gauge data are limited to certain stations and do not directly supply HAT/LAT for arbitrary locations, so they are less suitable for our purpose.)

## Calculating the Tidal Coefficient

Using the chosen API, the process to get the tidal coefficient is:

1. **Retrieve tide predictions for the day** – specifically the times and heights of high and low tides (extremes) for the location of interest. This gives us the daily high-water and low-water levels. For example, WorldTides can return a list of tide extremes within a date range ([WorldTides - Apidocs](https://www.worldtides.info/apidocs#:~:text=Get%20the%20tidal%20extremes%20referenced,and%20the%20datums)).

2. **Retrieve HAT and LAT datums for that location** – using the API’s datum information. WorldTides will return a list of datums including `"HAT"` and `"LAT"` with their heights relative to a reference level (by default Mean Sea Level, or you can specify a different reference datum) ([WorldTides - Datums](https://www.worldtides.info/datums#:~:text=HAT%20Highest%20Astronomical%20Tide%20The,highest%20predicted%20astronomical%20tide)). 

3. **Compute the daily tidal range** – subtract the lowest tide height from the highest tide height of the day.

4. **Compute the maximum range (HAT − LAT)** – using the HAT and LAT values. If the datum heights are given relative to Mean Sea Level, you can compute `HAT - LAT` by subtracting the LAT height (which may be negative) from the HAT height. *(Note: HAT and LAT themselves are typically reported relative to chart datum or another reference. The difference HAT–LAT is independent of reference datum.)*

5. **Calculate tidal coefficient** – apply the formula above to get a percentage. For example, if the daily range is 3.0 m and HAT−LAT for that location is 6.0 m, the coefficient would be (3.0/6.0)*100 = 50%, indicating the tide range is about half of the maximum possible for that site.

Below is a Python implementation using the **WorldTides API** to perform these steps. This script fetches the tide data and datums for a given latitude/longitude in the UK and then calculates the tidal coefficient:

```python
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
```

**How this works:** The code calls the WorldTides API with `extremes` (to get high/low tides) and `datums` (to get reference levels). For example, a response may include an array of `extremes` like: 

```json
"extremes": [
  {"dt": 1707745200, "date": "2025-02-12T04:00+0000", "height": 1.2, "type": "Low"},
  {"dt": 1707766800, "date": "2025-02-12T10:00+0000", "height": 5.4, "type": "High"},
  {"dt": 1707798600, "date": "2025-02-12T18:30+0000", "height": 1.5, "type": "Low"},
  {"dt": 1707820200, "date": "2025-02-12T00:30+0000", "height": 5.1, "type": "High"}
]
```

and a `datums` array like:

```json
"datums": [
  {"name": "LAT", "height": -1.20},
  {"name": "MLWS", "height": -0.90},
  … 
  {"name": "MSL", "height": 0.00},
  … 
  {"name": "HAT", "height": 5.80}
]
```

*(Note: The numbers above are illustrative.)* Here `HAT: 5.80 m` and `LAT: -1.20 m` are heights relative to Mean Sea Level, so **HAT − LAT = 7.00 m** would be the maximum tidal range. If the day’s highest tide is 5.4 m and lowest is 1.2 m, the daily range = 4.2 m. The tidal coefficient = (4.2 / 7.0) * 100 ≈ 60%. 

The script prints out the HAT, LAT, daily range, and the computed coefficient. You can adjust the date or use real-time dates as needed. This approach ensures you’re using a reliable data source (WorldTides, which aggregates official data) for any UK coastal coordinate, and it computes the tidal coefficient based on the **latest predictions and known tidal datums** for that location.

**Sources:**

- UK Hydrographic Office – *UK Tidal API* (covers 600+ UK tide stations, official predictions) ([UK Tidal API - Discovery - API Catalogue](https://www.api.gov.uk/ukho/uk-tidal-api-discovery/#:~:text=The%20ADMIRALTY%20UK%20Tidal%20API,stations%20around%20the%20United%20Kingdom)).  
- WorldTides API – global tide service providing tide **datums (including HAT/LAT)** and predictions for any lat/long ([WorldTides - Datums](https://www.worldtides.info/datums#:~:text=MHHWS%20Mean%20Higher%20High%20Water,The%20highest%20predicted%20astronomical%20tide)) ([WorldTides - Apidocs](https://www.worldtides.info/apidocs#:~:text=Get%20the%20tidal%20extremes%20referenced,and%20the%20datums)).  
- National Tidal & Sea Level Facility – definitions of HAT/LAT (tidal datum extremes over 19-year cycle) ([Definitions of tidal levels and other parameters | National Tidal and Sea Level Facility](https://ntslf.org/tides/definitions#:~:text=Highest%20astronomical%20tide%20,over%20a%20number%20of%20years)).