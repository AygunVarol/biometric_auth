from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import jwt
from functools import wraps
from redis import Redis

from models.models import User, BiometricData, db
from services.biometric_service import BiometricService
from utils.cache_manager import CacheManager
from config.config import Config

auth_bp = Blueprint('auth', __name__)
redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
cache = CacheManager(redis_client)
biometric_service = BiometricService()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def rate_limit(key_prefix, limit=5, period=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f"{key_prefix}:{request.remote_addr}"
            current = cache.get(key)
            
            if current is not None and int(current) >= limit:
                return jsonify({'message': 'Rate limit exceeded'}), 429
                
            cache.incr(key)
            if current is None:
                cache.expire(key, period)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/register', methods=['POST'])
@rate_limit('register')
def register():
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'face_data', 'voice_data')):
        return jsonify({'message': 'Missing required fields'}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
        
    try:
        new_user = User(username=data['username'])
        db.session.add(new_user)
        db.session.flush()
        
        biometric_data = BiometricData(
            user_id=new_user.id,
            face_template=biometric_service.process_face_data(data['face_data']),
            voice_template=biometric_service.process_voice_data(data['voice_data'])
        )
        db.session.add(biometric_data)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/authenticate', methods=['POST'])
@rate_limit('authenticate')
def authenticate():
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'biometric_data')):
        return jsonify({'message': 'Missing required fields'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    try:
        auth_result = biometric_service.verify_user(
            user.id,
            data['biometric_data']
        )
        
        if auth_result['success']:
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, Config.SECRET_KEY, algorithm="HS256")
            
            session['user_id'] = user.id
            
            return jsonify({
                'message': 'Authentication successful',
                'token': token
            }), 200
        else:
            return jsonify({
                'message': 'Authentication failed',
                'reason': auth_result['reason']
            }), 401
            
    except Exception as e:
        return jsonify({'message': f'Authentication error: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/update-biometrics', methods=['PUT'])
@token_required
@rate_limit('update_biometrics')
def update_biometrics(current_user):
    data = request.get_json()
    
    if not any(k in data for k in ('face_data', 'voice_data')):
        return jsonify({'message': 'No biometric data provided'}), 400
        
    try:
        biometric_data = BiometricData.query.filter_by(user_id=current_user.id).first()
        
        if 'face_data' in data:
            biometric_data.face_template = biometric_service.process_face_data(data['face_data'])
            
        if 'voice_data' in data:
            biometric_data.voice_template = biometric_service.process_voice_data(data['voice_data'])
            
        db.session.commit()
        return jsonify({'message': 'Biometric data updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Update failed: {str(e)}'}), 500
