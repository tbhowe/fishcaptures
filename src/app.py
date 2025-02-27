from flask import Flask, request, jsonify, g, render_template, redirect, url_for
from datetime import datetime, timedelta
import jwt
import traceback
from functools import wraps
from models import db, User, EnvironmentData
from celery_app import flask_app, celery
from tasks import fetch_env_data

app = flask_app
app.config['SECRET_KEY'] = 'your-secret-key'  # Change for production!

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
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
    # Read the optional is_admin flag; default to False if not provided.
    is_admin = data.get('is_admin', False)
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400
    
    # Create user with is_admin set according to the payload.
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

# Endpoint to log in and receive a JWT token.
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
        'user_id': str(user.id),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token})

# Endpoint to submit a timestamp and coordinates (associates the record with the current user).
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
        
        current_user = g.current_user
        env_data = EnvironmentData(timestamp=timestamp,
                                     latitude=lat,
                                     longitude=lng,
                                     status='pending',
                                     user_id=current_user.id)
        db.session.add(env_data)
        db.session.commit()
        
        # Queue the task for processing.
        fetch_env_data.apply_async(args=[env_data.id])
        return jsonify({'message': 'Data pending', 'id': env_data.id}), 202
    except Exception as e:
        print("Error occurred:", e)
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Endpoint for a user to view their own EnvironmentData.
@app.route('/my_data', methods=['GET'])
@token_required
def my_data():
    current_user = g.current_user
    records = EnvironmentData.query.filter_by(user_id=current_user.id).all()
    data = [record.to_dict() for record in records]
    return jsonify(data)

# Endpoint for an admin to view all EnvironmentData.
@app.route('/all_data', methods=['GET'])
@token_required
def all_data():
    current_user = g.current_user
    if not current_user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only.'}), 403
    records = EnvironmentData.query.all()
    data = [record.to_dict() for record in records]
    return jsonify(data)

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/delete_user/<user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    current_user = g.current_user
    if not current_user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only.'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found.'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'User {user_id} deleted successfully.'})

@app.route('/delete_record/<record_id>', methods=['DELETE'])
@token_required
def delete_record(record_id):
    current_user = g.current_user
    if not current_user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only.'}), 403
    
    record = EnvironmentData.query.get(record_id)
    if not record:
        return jsonify({'message': 'Record not found.'}), 404
    
    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': f'Record {record_id} deleted successfully.'})

# --- Additional Routes for Rendering Frontend Templates ---

# Landing page with login and register options.
@app.route('/')
def index():
    return render_template("index.html")

# Render the login page.
@app.route('/login_page')
def login_page():
    return render_template("login.html")

# Render the registration page.
@app.route('/register_page')
def register_page():
    return render_template("register.html")

if __name__ == '__main__':
    app.run(debug=False, port=5001)
