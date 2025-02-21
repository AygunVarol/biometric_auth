import redis
from typing import Optional, Any
from datetime import timedelta
from config.config import RedisConfig

class CacheManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=RedisConfig.REDIS_HOST,
            port=RedisConfig.REDIS_PORT,
            password=RedisConfig.REDIS_PASSWORD,
            decode_responses=True
        )

    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Set a key-value pair in cache with optional expiry
        
        Args:
            key: Cache key
            value: Value to store
            expiry: Expiry time in seconds
            
        Returns:
            bool: Success status
        """
        try:
            if expiry:
                return self.redis_client.setex(key, expiry, value)
            return self.redis_client.set(key, value)
        except redis.RedisError:
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get value for a key from cache
        
        Args:
            key: Cache key
            
        Returns:
            Optional[str]: Cached value if exists
        """
        try:
            return self.redis_client.get(key)
        except redis.RedisError:
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: Success status
        """
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError:
            return False

    def set_auth_attempt(self, user_id: str, attempt_count: int) -> bool:
        """
        Set authentication attempt count for rate limiting
        
        Args:
            user_id: User identifier
            attempt_count: Number of attempts
            
        Returns:
            bool: Success status
        """
        key = f"auth_attempt:{user_id}"
        return self.set(key, attempt_count, expiry=300)  # 5 minute expiry

    def get_auth_attempt(self, user_id: str) -> int:
        """
        Get authentication attempt count
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of attempts
        """
        key = f"auth_attempt:{user_id}"
        count = self.get(key)
        return int(count) if count else 0

    def set_session(self, session_id: str, user_data: dict, expiry: int = 3600) -> bool:
        """
        Store session data with expiry
        
        Args:
            session_id: Session identifier
            user_data: User session data
            expiry: Session expiry in seconds
            
        Returns:
            bool: Success status
        """
        key = f"session:{session_id}"
        return self.set(key, str(user_data), expiry)

    def get_session(self, session_id: str) -> Optional[str]:
        """
        Retrieve session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[str]: Session data if exists
        """
        key = f"session:{session_id}"
        return self.get(key)

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: Success status
        """
        key = f"session:{session_id}"
        return self.delete(key)

    def store_biometric_temp(self, user_id: str, biometric_data: str, 
                           expiry: int = 300) -> bool:
        """
        Temporarily store biometric data during authentication
        
        Args:
            user_id: User identifier
            biometric_data: Biometric template data
            expiry: Data expiry in seconds
            
        Returns:
            bool: Success status
        """
        key = f"biometric_temp:{user_id}"
        return self.set(key, biometric_data, expiry)

    def cleanup(self):
        """Close Redis connection"""
        try:
            self.redis_client.close()
        except redis.RedisError:
            pass
