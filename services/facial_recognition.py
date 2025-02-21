import cv2
import dlib
import numpy as np
from typing import Tuple, Optional, List
import logging
from datetime import datetime
import os

class FacialRecognition:
    def __init__(self):
        # Initialize face detector and facial landmarks predictor
        self.face_detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')
        self.face_recognizer = dlib.face_recognition_model_v1('models/dlib_face_recognition_resnet_model_v1.dat')
        
        # Parameters for blink detection
        self.EYE_AR_THRESH = 0.3
        self.EYE_AR_CONSEC_FRAMES = 3
        
        # Initialize logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def detect_face(self, image: np.ndarray) -> Optional[dlib.rectangle]:
        """Detect face in image and return bounding box"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector(gray)
            
            if len(faces) == 0:
                return None
                
            return faces[0]  # Return first detected face
            
        except Exception as e:
            self.logger.error(f"Error in face detection: {str(e)}")
            return None

    def get_facial_landmarks(self, image: np.ndarray, face: dlib.rectangle) -> np.ndarray:
        """Extract facial landmarks from detected face"""
        shape = self.shape_predictor(image, face)
        return np.array([[p.x, p.y] for p in shape.parts()])

    def eye_aspect_ratio(self, eye_landmarks: np.ndarray) -> float:
        """Calculate eye aspect ratio for blink detection"""
        # Compute euclidean distances between vertical eye landmarks
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        # Compute euclidean distance between horizontal eye landmarks
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        # Calculate eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear

    def detect_blink(self, landmarks: np.ndarray) -> bool:
        """Detect if person is blinking using facial landmarks"""
        # Extract eye regions from landmarks
        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        
        # Calculate eye aspect ratios
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        
        # Average eye aspect ratio
        ear = (left_ear + right_ear) / 2.0
        
        return ear < self.EYE_AR_THRESH

    def extract_face_encoding(self, image: np.ndarray, face: dlib.rectangle) -> np.ndarray:
        """Extract face encoding for face recognition"""
        try:
            shape = self.shape_predictor(image, face)
            face_encoding = np.array(self.face_recognizer.compute_face_descriptor(image, shape))
            return face_encoding
            
        except Exception as e:
            self.logger.error(f"Error extracting face encoding: {str(e)}")
            return None

    def compare_faces(self, known_encoding: np.ndarray, candidate_encoding: np.ndarray, 
                     threshold: float = 0.6) -> bool:
        """Compare face encodings to determine match"""
        if known_encoding is None or candidate_encoding is None:
            return False
            
        # Calculate euclidean distance between encodings
        distance = np.linalg.norm(known_encoding - candidate_encoding)
        return distance < threshold

    def verify_liveness(self, image: np.ndarray, face: dlib.rectangle) -> bool:
        """Verify liveness through blink detection and other anti-spoofing measures"""
        try:
            landmarks = self.get_facial_landmarks(image, face)
            
            # Check for natural facial variations/micro-movements
            is_blinking = self.detect_blink(landmarks)
            
            # Additional anti-spoofing checks could be added here
            # e.g. texture analysis, depth detection, etc.
            
            return is_blinking
            
        except Exception as e:
            self.logger.error(f"Error in liveness verification: {str(e)}")
            return False

    def process_authentication(self, image: np.ndarray, stored_encoding: np.ndarray) -> Tuple[bool, str]:
        """Process complete facial authentication including liveness detection"""
        try:
            # Detect face
            face = self.detect_face(image)
            if face is None:
                return False, "No face detected"
                
            # Verify liveness
            if not self.verify_liveness(image, face):
                return False, "Liveness check failed"
                
            # Extract and compare face encoding
            candidate_encoding = self.extract_face_encoding(image, face)
            if candidate_encoding is None:
                return False, "Failed to extract face features"
                
            # Compare with stored encoding
            if not self.compare_faces(stored_encoding, candidate_encoding):
                return False, "Face match failed"
                
            return True, "Authentication successful"
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False, f"Authentication error: {str(e)}"
