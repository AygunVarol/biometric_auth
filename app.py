from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config.config import Config
from models.models import db
from services.biometric_service import BiometricService
from services.facial_recognition import FacialRecognition
from services.voice_recognition import VoiceRecognition
from controllers.auth_controller import auth_bp
from utils.cache_manager import cache
from utils.db_utils import init_db
import logging

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
redis_client = FlaskRedis(app)
cache.init_app(app)

# Initialize services
facial_recognition = FacialRecognition()
voice_recognition = VoiceRecognition()
biometric_service = BiometricService(facial_recognition, voice_recognition)

# Register blueprints
app.register_blueprint(auth_bp)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.before_first_request
def setup():
    """Initialize database and cache on first request"""
    init_db(app)
    cache.clear()
    logger.info("Application initialized successfully")

@app.route('/')
def index():
    """Render main authentication page"""
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    """Render dashboard for authenticated users"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
