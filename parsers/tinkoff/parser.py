from typing import Optional, Tuple, List
from datetime import datetime
import re
from os import getcwd, path

from bs4 import BeautifulSoup

from parsers.tinkoff.config import generate_url, generate_post_url, SOURCE
from entities.news import NewsDTO
from utils.requests_with_proxy import try_to_make_get


def parse_special_news(id: str) -> Tuple[str, str, List[str]]:
    r = try_to_make_get(generate_post_url(id))
    title = r.json()["payload"]["content"]["title"]
    bs4 = BeautifulSoup(r.json()["payload"]["content"]["body"], features="html.parser")
    links = []
    for link in bs4.findAll("a"):
        if not link.text == "Весь текст дисклеймера" and link.has_attr("href"):
            links.append(link["href"])
    text = bs4.text
    return title, text, links


def parse_page(cursor: Optional[str]):
    re_links = re.compile(
        r"(?P<url>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/=]*))"
    )
    r = try_to_make_get(generate_url(cursor))
    next_cursor = r.json()["payload"]["nextCursor"]
    print(f"Next cursor: {next_cursor}")
    news = []
    for post in r.json()["payload"]["items"]:
        news_id = post["id"]
        link = f"https://www.tinkoff.ru/invest/social/profile/Tinkoff_Investments/{news_id}/"
        post_date = datetime.fromisoformat(
            post["inserted"].split(".")[0] + "+" + post["inserted"].split(".")[1].split("+")[1]
        )
        if post["content"]["type"] == "simple":
            text = post["content"]["text"]
            title = ""
            links = [match[0] for match in re_links.findall(text)]
        elif post["content"]["type"] in ["news", "review"]:
            title, text, links = parse_special_news(news_id)
        else:
            print(post["content"]["type"], link, cursor)
            continue
        _news = NewsDTO(link=link, text=text, title=title, source=SOURCE, timestamp=post_date, refers_to=links)
        dump_news(_news)
        news.append(_news)
    return next_cursor, news


def parse_all() -> List[NewsDTO]:
    next_cursor, news = parse_page(None)
    while next_cursor:
        print(len(news), news[-1].timestamp)
        try:
            next_cursor, batch = parse_page(next_cursor)
        except Exception as e:
            print(e)
            print(f"Timeout: {next_cursor}")
            break
        news.extend(batch)
    return news


def dump_news(news: NewsDTO):
    link = news.link.replace("/", "_").replace(":", "")
    p = path.join(getcwd(), "parsers/tinkoff/dumps", f"{link}.json")
    with open(p, "w", encoding="utf-8") as file:
        print(f"Stored to {p}")
        file.write(news.json(ensure_ascii=False))
