from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # Relationships
    biometric_data = relationship("BiometricData", back_populates="user")
    auth_logs = relationship("AuthenticationLog", back_populates="user")

class BiometricData(Base):
    __tablename__ = 'biometric_data'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    face_template = Column(Binary)
    voice_template = Column(Binary)
    last_updated = Column(DateTime, default=datetime.utcnow)
    template_version = Column(String(10))
    is_primary = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="biometric_data")

class AuthenticationLog(Base):
    __tablename__ = 'authentication_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    auth_type = Column(String(20))  # face, voice, or multi-factor
    success = Column(Boolean)
    failure_reason = Column(String(100))
    device_info = Column(String(200))
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User", back_populates="auth_logs")

class SecuritySettings(Base):
    __tablename__ = 'security_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    require_blink_detection = Column(Boolean, default=True)
    require_voice_verification = Column(Boolean, default=False)
    max_failed_attempts = Column(Integer, default=3)
    lockout_duration_minutes = Column(Integer, default=30)
    last_modified = Column(DateTime, default=datetime.utcnow)
