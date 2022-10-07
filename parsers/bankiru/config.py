from typing import Union
from datetime import datetime, date

BASE_URL = "https://www.banki.ru/news/lenta/business/"

def generate_url_date(d: Union[datetime, date]) -> str:
    additional_url = f"?filterType=all&d={d.day}&m={d.month}&y={d.year}"
    return BASE_URL + additional_url
