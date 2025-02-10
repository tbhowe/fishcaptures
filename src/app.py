from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta
import jwt
import traceback
from functools import wraps
from models import db, User, EnvironmentData
from celery_app import flask_app, celery
from tasks import fetch_env_data

app = flask_app
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production!

# A decorator to require a valid JWT token on endpoints.
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Expect the header "Authorization: Bearer <token>"
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if current_user is None:
                return jsonify({'message': 'User not found!'}), 401
            g.current_user = current_user
        except Exception as e:
            print(e)
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)
    return decorated

# Endpoint to register a new user.
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400
    
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

# Endpoint to log in and get a JWT token.
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token})

# Protected endpoint to submit a timestamp and coordinates.
@app.route('/submit_timestamp', methods=['POST'])
@token_required
def submit_timestamp():
    try:
        data = request.get_json()
        timestamp_str = data.get('timestamp')
        timestamp = datetime.fromisoformat(timestamp_str)
        
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is None or lng is None:
            return jsonify({'error': "Missing 'lat' or 'lng'"}), 400
        lat = float(lat)
        lng = float(lng)
        
        # Associate the data with the currently authenticated user.
        current_user = g.current_user
        env_data = EnvironmentData(timestamp=timestamp,
                                     latitude=lat,
                                     longitude=lng,
                                     status='pending',
                                     user_id=current_user.id)
        db.session.add(env_data)
        db.session.commit()
        
        # Queue the task to process this record.
        fetch_env_data.apply_async(args=[env_data.id])
        return jsonify({'message': 'Data pending', 'id': env_data.id}), 202
    except Exception as e:
        print("Error occurred:", e)
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5001)
