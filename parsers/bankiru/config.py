from typing import Union
from datetime import datetime, date

BASE_URL = "https://www.banki.ru/news/lenta/"
SOURCE = "BANKIRU"


def generate_url_date(d: Union[datetime, date]) -> str:
    additional_url = f"business/?filterType=all&d={d.day}&m={d.month}&y={d.year}"
    return BASE_URL + additional_url


def generate_news_url(id: str) -> str:
    additional_url = f"?id={id}"
    return BASE_URL + additional_url
