import os
from dotenv import load_load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/biometric_auth')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '5'))
    DATABASE_POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))

    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Facial recognition settings
    FACE_DETECTION_CONFIDENCE = float(os.getenv('FACE_DETECTION_CONFIDENCE', '0.8'))
    FACE_MATCHING_THRESHOLD = float(os.getenv('FACE_MATCHING_THRESHOLD', '0.6'))
    REQUIRED_FACE_FEATURES = int(os.getenv('REQUIRED_FACE_FEATURES', '68'))
    
    # Voice recognition settings
    VOICE_SAMPLE_RATE = int(os.getenv('VOICE_SAMPLE_RATE', '16000'))
    VOICE_MATCHING_THRESHOLD = float(os.getenv('VOICE_MATCHING_THRESHOLD', '0.75'))
    
    # Security settings
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '3'))
    LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION', '300'))  # seconds
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '1800'))  # seconds
    
    # Biometric template storage
    TEMPLATE_STORAGE_PATH = os.getenv('TEMPLATE_STORAGE_PATH', 'storage/biometric_templates')
    MAX_TEMPLATE_SIZE = int(os.getenv('MAX_TEMPLATE_SIZE', '50000'))  # bytes
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/biometric_auth.log')
    
    # Anti-spoofing settings
    LIVENESS_CHECK_ENABLED = os.getenv('LIVENESS_CHECK_ENABLED', 'True').lower() == 'true'
    BLINK_DETECTION_THRESHOLD = float(os.getenv('BLINK_DETECTION_THRESHOLD', '0.3'))
    MIN_BLINKS_REQUIRED = int(os.getenv('MIN_BLINKS_REQUIRED', '2'))

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/biometric_auth_test'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
