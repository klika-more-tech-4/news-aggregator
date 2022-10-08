from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Text, Integer, ARRAY

Base = declarative_base()


class NewsModel(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    link = Column(String, index=True, nullable=False)
    text = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    refers_to = Column(ARRAY(String), nullable=False)
