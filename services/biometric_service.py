from typing import Dict, Optional, Tuple
import logging
from datetime import datetime

from ..models.models import User, BiometricData
from .facial_recognition import FacialRecognitionService
from .voice_recognition import VoiceRecognitionService
from ..utils.cache_manager import CacheManager
from ..utils.db_utils import get_db_session
from ..config.config import BiometricConfig

logger = logging.getLogger(__name__)

class BiometricService:
    def __init__(self):
        self.facial_recognition = FacialRecognitionService()
        self.voice_recognition = VoiceRecognitionService()
        self.cache = CacheManager()
        self.config = BiometricConfig()

    async def verify_user(self, user_id: int, face_data: bytes, 
                         voice_data: Optional[bytes] = None) -> Tuple[bool, str]:
        """
        Verify user identity using multiple biometric factors
        Returns: (success: bool, message: str)
        """
        try:
            db = get_db_session()
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"

            biometric_data = db.query(BiometricData).filter(
                BiometricData.user_id == user_id).first()
            if not biometric_data:
                return False, "No biometric data enrolled"

            # Check for recent failed attempts
            failed_attempts = self.cache.get_failed_attempts(user_id)
            if failed_attempts >= self.config.MAX_FAILED_ATTEMPTS:
                return False, "Too many failed attempts. Please try again later"

            # Facial recognition check
            face_match = await self.facial_recognition.verify_face(
                face_data, biometric_data.facial_data)
            if not face_match:
                self._record_failed_attempt(user_id)
                return False, "Face verification failed"

            # Optional voice verification
            if voice_data and biometric_data.voice_data:
                voice_match = await self.voice_recognition.verify_voice(
                    voice_data, biometric_data.voice_data)
                if not voice_match:
                    self._record_failed_attempt(user_id)
                    return False, "Voice verification failed"

            # Update successful authentication
            self._record_successful_auth(user_id)
            return True, "Verification successful"

        except Exception as e:
            logger.error(f"Error in biometric verification: {str(e)}")
            return False, "Internal verification error"
        finally:
            db.close()

    async def enroll_user(self, user_id: int, face_data: bytes,
                         voice_data: Optional[bytes] = None) -> Tuple[bool, str]:
        """
        Enroll user biometric data
        Returns: (success: bool, message: str)
        """
        try:
            db = get_db_session()
            
            # Validate face data quality
            face_quality = await self.facial_recognition.check_quality(face_data)
            if not face_quality:
                return False, "Face image quality insufficient"

            # Process and store biometric data
            facial_template = await self.facial_recognition.create_template(face_data)
            
            voice_template = None
            if voice_data:
                voice_quality = await self.voice_recognition.check_quality(voice_data)
                if not voice_quality:
                    return False, "Voice sample quality insufficient"
                voice_template = await self.voice_recognition.create_template(voice_data)

            # Store or update biometric data
            biometric_data = db.query(BiometricData).filter(
                BiometricData.user_id == user_id).first()
            
            if biometric_data:
                biometric_data.facial_data = facial_template
                biometric_data.voice_data = voice_template
                biometric_data.updated_at = datetime.utcnow()
            else:
                biometric_data = BiometricData(
                    user_id=user_id,
                    facial_data=facial_template,
                    voice_data=voice_template
                )
                db.add(biometric_data)

            db.commit()
            return True, "Enrollment successful"

        except Exception as e:
            db.rollback()
            logger.error(f"Error in biometric enrollment: {str(e)}")
            return False, "Internal enrollment error"
        finally:
            db.close()

    def _record_failed_attempt(self, user_id: int) -> None:
        """Record failed authentication attempt"""
        current_attempts = self.cache.get_failed_attempts(user_id)
        self.cache.set_failed_attempts(user_id, current_attempts + 1)
        logger.warning(f"Failed authentication attempt for user {user_id}")

    def _record_successful_auth(self, user_id: int) -> None:
        """Record successful authentication"""
        self.cache.clear_failed_attempts(user_id)
        self.cache.set_last_success(user_id, datetime.utcnow())
        logger.info(f"Successful authentication for user {user_id}")
