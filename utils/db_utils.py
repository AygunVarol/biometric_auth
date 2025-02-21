from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
from typing import Generator

from config.config import DatabaseConfig
from models.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._initialize_db()
        return cls._instance

    @classmethod
    def _initialize_db(cls) -> None:
        try:
            cls._engine = create_engine(
                DatabaseConfig.DATABASE_URI,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
            
            Base.metadata.create_all(cls._engine)
            
            cls._session_factory = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=cls._engine
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    @contextmanager
    def get_session(self) -> Generator:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: dict = None) -> list:
        with self.get_session() as session:
            try:
                result = session.execute(query, params or {})
                return result.fetchall()
            except Exception as e:
                logger.error(f"Query execution error: {str(e)}")
                raise

    def cleanup_connections(self) -> None:
        try:
            if self._engine:
                self._engine.dispose()
        except Exception as e:
            logger.error(f"Failed to cleanup database connections: {str(e)}")
            raise

    @classmethod
    def get_engine(cls):
        if not cls._engine:
            cls._initialize_db()
        return cls._engine

    def health_check(self) -> bool:
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
