from flask import Flask, request, jsonify
from datetime import datetime
from models import db, EnvironmentData
from celery_app import flask_app, celery
from tasks import fetch_env_data
import traceback

app = flask_app

@app.route('/submit_timestamp', methods=['POST'])
def submit_timestamp():
    try:
        data = request.get_json()
        timestamp_str = data.get('timestamp')
        timestamp = datetime.fromisoformat(timestamp_str)
        
        # Extract latitude and longitude from the request.
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is None or lng is None:
            raise Exception("Missing 'lat' or 'lng' in request.")
        lat = float(lat)
        lng = float(lng)
        
        # Create a record that now includes coordinates.
        env_data = EnvironmentData(timestamp=timestamp, latitude=lat, longitude=lng, status='pending')
        db.session.add(env_data)
        db.session.commit()

        # Queue the Celery task using the new record ID.
        fetch_env_data.apply_async(args=[env_data.id])
        return jsonify({'message': 'Data pending', 'id': env_data.id}), 202
    except Exception as e:
        print("Error occurred:", e)
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5001)
