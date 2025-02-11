# fishcaptures
## Auto-logging of environmental data for timestamped fish captures



Fishcaptures is a tool for auto-logging environmental data tied to timestamped fish captures. It records the time and location of a catch and then retrieves environmental data from tide, weather, and astronomy APIs. This helps anglers track the conditions around where their fish were caught.

> **Disclaimer: This project is in early development and not yet install-ready. Use at your own risk!**

## How It Works

1. **User Registration & Login:**  
   Users register using the `/register` endpoint and log in via `/login` to receive a JWT token.

2. **Data Submission:**  
   After logging in, users submit a timestamp and coordinates (latitude and longitude) via the `/submit_timestamp` endpoint. This creates an `EnvironmentData` record linked to the user.

3. **Background Processing:**  
   A background task, run with Celery (using Redis as the broker), fetches additional environmental data from tide, weather, and astronomy APIs. Once all data is gathered, the record status is updated to "complete".

4. **Data Viewing & Administration:**  
   - Users can view their own records using the `/my_data` endpoint.  
   - Admins can view all records with `/all_data` and delete users or records using `/delete_user/<user_id>` and `/delete_record/<record_id>`.

## Main Classes and Files

- **User (in `models.py`):**  
  Represents a user with properties such as `username`, `email`, and a hashed password. It includes methods to set and check passwords.

- **EnvironmentData (in `models.py`):**  
  Stores details of each fish capture along with environmental data. Its fields include:
  - **Basic Information:**  
    `timestamp`, `latitude`, `longitude`, and `status`.
  - **Tide Data:**  
    `currentTideHeight`, `tideHour`, `maxHighTide`, `minLowTide`.
  - **Weather Data:**  
    `airTemperature`, `pressure`, `cloudCover`, `currentDirection`, `currentSpeed`, `swellDirection`, `swellHeight`, `swellPeriod`, `secondarySwellPeriod`, `secondarySwellDirection`, `secondarySwellHeight`, `waveDirection`, `waveHeight`, `wavePeriod`, `windWaveDirection`, `windWaveHeight`, `windWavePeriod`, `windDirection`, `windSpeed`, and `gust`.
  - **Astronomy Data:**  
    `sunrise`, `sunset`, `moonrise`, `moonset`, `moonFraction`, `currentMoonPhaseText`, `currentMoonPhaseValue`, and `lightLevel`.

- **API Endpoints (in `app.py`):**  
  Handles user registration, login, data submission, and data retrieval.

- **Background Tasks (in `tasks.py`):**  
  Uses Celery to asynchronously fetch environmental data from external APIs and update the corresponding `EnvironmentData` record.

- **Celery Setup (in `celery_app.py`):**  
  Configures Celery to use Redis as the message broker and result backend, and integrates it with the Flask application.

## Data Captured

The application gathers environmental data based on the provided timestamp and location:
- **Tide Information:**  
  Current tide height, tide hour, maximum high tide, and minimum low tide.
- **Weather Information:**  
  Air temperature, atmospheric pressure, cloud cover, wind and swell details (directions, speeds, heights, and periods).
- **Astronomy Information:**  
  Sunrise, sunset, moonrise, moonset, moon phase details, and light level.


