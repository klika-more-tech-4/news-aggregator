from typing import Any, List

from pydantic import BaseModel

from parsers.tinkoff.parser import parse_page, parse_special_news


class TempModel(BaseModel):
    tinkoff: List[Any]


if __name__ == "__main__":
    next_cursor, news = parse_page(None)
    while next_cursor:
        print(next_cursor, len(news))
        try:
            next_cursor, batch = parse_page(next_cursor)
            news.extend(batch)
        except KeyboardInterrupt:
            next_cursor = None
    with open("output.json", "w", encoding="utf-8") as file:
        file.write(TempModel(tinkoff=news).json(ensure_ascii=False))
