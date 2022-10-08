from .app import app

from fastapi import Path

from sqlmodel import Session, select
from database import NewsModel, engine

from entities.news import NewsDTO


@app.post("/news")
def create_news(news: NewsDTO):
    with Session(engine) as session:
        news_model = NewsModel(
            link=news.link,
            text=news.text,
            title=news.title,
            source=news.source,
            timestamp=news.timestamp,
            refers_to=news.refers_to,
        )
        session.add(news_model)
        session.commit()
        session.refresh(news_model)
        return news_model


@app.get("/news/{news_id}")
def get_news(news_id: int = Path(title="Id of the news")):
    with Session(engine) as session:
        q = select(NewsModel).where(NewsModel.id == news_id)
        result = session.exec(q)
        return result.first()
