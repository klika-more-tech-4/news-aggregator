from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import settings

from .models import *

engine = create_engine(settings.db_uri)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = (
    engine,
    SessionLocal,
    NewsModel,
)
