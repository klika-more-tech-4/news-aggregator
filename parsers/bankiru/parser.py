from datetime import datetime, timedelta
from os import getcwd, path
from typing import List
import re

import requests
from bs4 import BeautifulSoup, SoupStrainer
from pydantic import BaseModel

from parsers.bankiru.config import generate_url_date, generate_news_url, SOURCE
from entities.news import NewsDTO


def parse_news_for_date(d: datetime) -> List[str]:
    ids = []
    link_re = re.compile("\/news\/lenta\/\?id=([0-9]{1,})")
    page = 0
    while True:
        ids_on_page = 0
        page += 1
        r = requests.get(generate_url_date(d) + f"&page={page}")
        for link in BeautifulSoup(r.text, parse_only=SoupStrainer("a"), features="html.parser"):
            if link.has_attr("href"):
                try:
                    ids.append(link_re.match(link["href"]).group(1))
                    ids_on_page += 1
                except:
                    pass

        if ids_on_page == 0:
            break
    return list(set(ids))


def parse_single_news(id: str) -> NewsDTO:
    link = generate_news_url(id)
    r = requests.get(link)
    bs4 = BeautifulSoup(r.text, features="html.parser")
    title = bs4.find_all("h1", {"class": "text-header-0"})[0].text
    creation_date = datetime.strptime(
        (
            bs4.find_all("div", {"style": "padding-top: 24px;"})[0]
            .findChildren("div", recursive=False)[0]  # Тулбар
            .findChildren("div", recursive=False)[1]  # Правая часть с датой и просмотрами
            .findChildren("span")[0]  # Дата
            .text.strip()
        ),
        "%d.%m.%Y %H:%M",
    )
    links = []
    text = []
    for paragraph in bs4.find_all("div", {"itemprop": "articleBody"})[0].findChildren("p", recursive=False):
        for a_link in paragraph.find_all("a"):
            if a_link.has_attr("href") and "mailto:" not in a_link["href"]:
                if a_link["href"][0] == "/":
                    links.append("https://www.banki.ru" + a_link["href"])
                else:
                    links.append(a_link["href"])
        text.append(paragraph.text)

    return NewsDTO(
        link=link, text="\n".join(text), title=title, source=SOURCE, timestamp=creation_date, refers_to=links
    )


class BankiRUNews(BaseModel):
    bankiru: List[NewsDTO]


def parse_all(start_date: datetime):
    date = start_date
    while date < datetime.now():
        news = []
        ids = parse_news_for_date(date)
        print(date, len(ids))
        if len(ids) > 0:
            for id in ids:
                news.append(parse_single_news(id))
            with open(
                path.join(getcwd(), "parsers/bankiru/dumps", f"{date.isoformat()}.json"), "w", encoding="utf-8"
            ) as file:
                file.write(BankiRUNews(bankiru=news).json(ensure_ascii=False))
        date = date + timedelta(days=1)
