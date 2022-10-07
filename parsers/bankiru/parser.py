from datetime import datetime
from typing import List
import re

import requests
from bs4 import BeautifulSoup, SoupStrainer

from parsers.bankiru.config import generate_url_date, generate_news_url, SOURCE
from entities.news import NewsDTO


def parse_news_for_date(d: datetime) -> List[str]:
    ids = []
    link_re = re.compile("\/news\/lenta\/\?id=([0-9]{1,})")
    r = requests.get(generate_url_date(d))
    for link in BeautifulSoup(r.text, parse_only=SoupStrainer("a"), features="html.parser"):
        if link.has_attr("href"):
            try:
                ids.append(link_re.match(link["href"]).group(1))
            except:
                pass
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
            if "mailto:" not in a_link["href"]:
                links.append(a_link["href"])
        text.append(paragraph.text)

    return NewsDTO(
        link=link, text="\n".join(text), title=title, source=SOURCE, timestamp=creation_date, refers_to=links
    )
