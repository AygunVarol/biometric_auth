import os
import librosa
import numpy as np
from scipy.io import wavfile
from python_speech_features import mfcc
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceRecognitionService:
    def __init__(self):
        self.sample_rate = 16000
        self.n_mfcc = 13
        self.scaler = StandardScaler()
        
    def extract_features(self, audio_path: str) -> Optional[np.ndarray]:
        """Extract MFCC features from audio file"""
        try:
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract MFCC features
            mfcc_features = mfcc(audio, 
                               samplerate=sr,
                               numcep=self.n_mfcc,
                               nfilt=26,
                               nfft=1024)
            
            # Normalize features
            mfcc_scaled = self.scaler.fit_transform(mfcc_features)
            
            return mfcc_scaled
            
        except Exception as e:
            logger.error(f"Error extracting voice features: {str(e)}")
            return None

    def compare_voices(self, voice1_features: np.ndarray, 
                      voice2_features: np.ndarray) -> Tuple[float, bool]:
        """Compare two voice feature sets and return similarity score"""
        try:
            # Dynamic time warping distance
            distance = self._dtw_distance(voice1_features, voice2_features)
            
            # Convert distance to similarity score (0-1)
            similarity = 1 / (1 + distance)
            
            # Threshold for match
            threshold = 0.75
            is_match = similarity >= threshold
            
            return similarity, is_match
            
        except Exception as e:
            logger.error(f"Error comparing voices: {str(e)}")
            return 0.0, False
            
    def _dtw_distance(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate DTW distance between two feature sets"""
        r, c = len(x), len(y)
        D = np.zeros((r + 1, c + 1))
        D[0, :] = np.inf
        D[:, 0] = np.inf
        D[0, 0] = 0
        
        for i in range(r):
            for j in range(c):
                dist = np.linalg.norm(x[i] - y[j])
                D[i + 1, j + 1] = dist + min(D[i, j + 1],    # insertion
                                           D[i + 1, j],    # deletion
                                           D[i, j])        # match
                                           
        return D[r, c]

    def verify_voice(self, enrolled_path: str, 
                    verification_path: str) -> Tuple[bool, float]:
        """Verify if two voice recordings match"""
        try:
            # Extract features
            enrolled_features = self.extract_features(enrolled_path)
            verify_features = self.extract_features(verification_path)
            
            if enrolled_features is None or verify_features is None:
                return False, 0.0
                
            # Compare features
            similarity, is_match = self.compare_voices(enrolled_features, 
                                                     verify_features)
            
            return is_match, similarity
            
        except Exception as e:
            logger.error(f"Error in voice verification: {str(e)}")
            return False, 0.0
            
    def enroll_voice(self, audio_path: str) -> Optional[np.ndarray]:
        """Enroll a voice sample and return features for storage"""
        try:
            features = self.extract_features(audio_path)
            if features is not None:
                return features.flatten()
            return None
            
        except Exception as e:
            logger.error(f"Error enrolling voice: {str(e)}")
            return None

    def is_live_voice(self, audio_path: str) -> bool:
        """Check if voice sample is from a live person vs recording"""
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract features indicating live voice
            zero_crossings = librosa.zero_crossings(audio).sum()
            rms_energy = librosa.feature.rms(y=audio)[0].mean()
            
            # Thresholds for live voice detection
            zc_threshold = 1000
            rms_threshold = 0.05
            
            return (zero_crossings > zc_threshold and 
                   rms_energy > rms_threshold)
                   
        except Exception as e:
            logger.error(f"Error in liveness detection: {str(e)}")
            return False
