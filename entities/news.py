from pydantic import BaseModel, HttpUrl, Field
import datetime as dt


class NewsDTO(BaseModel):
    link: HttpUrl = Field(..., description="Ссылка на новость")
    text: str = Field(..., description="Текст новости")
    title: str = Field(..., description="Заголовок новости")
    source: str = Field(..., description="Источник новости")
    timestamp: dt.datetime = Field(..., description="Время публикации")
    refers_to: list[HttpUrl] = Field(..., description="Все ссылки в тексте")
