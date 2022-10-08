from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Text, Integer, ARRAY

Base = declarative_base()


class NewsModel(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    link = Column(String, index=True, nullable=False)
    text = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    refers_to = Column(ARRAY(String), nullable=False)


class TelegramUserModel(Base):
    __tablename__ = "telegram_users"

    id = Column(String, primary_key=True)
    chat_id = Column(Integer)
    state = Column(String, nullable=False, default="NEW")
    last_message_id = Column(Integer, nullable=True)
    okveds = Column(ARRAY(String), nullable=True)
