from datetime import date

from parsers.bankiru.config import generate_url

def test_url_assembler():
    d = date(
        year=2022,
        month=1,
        day=4
    )
    assert generate_url(d) == f"https://www.banki.ru/news/lenta/business/?filterType=all&d={d.day}&m={d.month}&y={d.year}"
