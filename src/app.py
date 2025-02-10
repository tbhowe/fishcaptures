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

        env_data = EnvironmentData(timestamp=timestamp, status='pending')
        db.session.add(env_data)
        db.session.commit()

        # Using apply_async for better error visibility
        fetch_env_data.apply_async(args=[env_data.id])

        return jsonify({'message': 'Data pending', 'id': env_data.id}), 202
    except Exception as e:
        # Full traceback logging for debugging
        print("Error occurred:", e)
        print(traceback.format_exc())  # Captures full error stack
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, port=5001)


