import datetime as dt
import json
import logging
import time
from typing import Iterator

import dateparser
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, HttpUrl

from entities.news import NewsDTO

logger = logging.getLogger(__name__)

GARANT_HOSTNAME = 'www.garant.ru'
GARANT_INDEX_URL = f'https://{GARANT_HOSTNAME}'
GARANT_NEWS_URL = f'{GARANT_INDEX_URL}/news/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/106.0.0.0 Safari/537.36',
}

TIMEOUT = 0


class ArticleContent(BaseModel):
    title: str
    text: str
    refers_to: list[HttpUrl]


class ArticlePreviewContent(BaseModel):
    url: HttpUrl
    timestamp: dt.datetime


def get_news() -> Iterator[NewsDTO]:
    response = requests.get(GARANT_NEWS_URL, headers=HEADERS)
    if not (200 <= response.status_code < 300):
        logger.error(f"Плохой ответ: {response=}")
        return
    soup = BeautifulSoup(response.text, features="html.parser")
    is_last_page = True
    for article_preview in soup.select_one('.feed .section-inner').children:  # type: Tag
        if not isinstance(article_preview, Tag):
            continue
        is_last_page = False
        try:
            yield handle_article(article_preview)
        except Exception as e:
            logger.error(f"Не удалось обработать новость: {e=}", exc_info=True)
    pagination = soup.select_one('.pagination .pagination-next')
    params = {
        "form_data[source]": pagination.attrs['data-source'],
        "form_data[source_id]": pagination.attrs['data-source_id'],
        "form_data[last_oid]": pagination.attrs['data-last_oid'],
        "form_data[last_val]": pagination.attrs['data-last_val'],
        "form_data[version]": pagination.attrs['data-version'],
        "form_data[url]": '/news/',
    }
    while not is_last_page:
        time.sleep(TIMEOUT)
        response = requests.get(
            f"{GARANT_INDEX_URL}/ajax/pagination/",
            params=params,
            headers=HEADERS
        )
        if not (200 <= response.status_code < 300):
            logger.error(f"Плохой ответ: {response=}")
            return
        response = response.text.split('|')
        payload = json.loads(response[1])
        params['form_data[last_oid]'] = payload['last_oid']
        params['form_data[last_val]'] = payload['last_val']
        is_last_page = payload['is_last_page']
        for article_preview_html in payload['items']:
            article_preview = BeautifulSoup(article_preview_html, features="html.parser")
            try:
                yield handle_article(article_preview)
            except Exception as e:
                logger.error(f"Не удалось обработать новость: {e=}", exc_info=True)


def handle_article(article_preview: Tag) -> NewsDTO:
    article_preview_content = parse_article_preview(article_preview)
    article = parse_article(article_preview_content.url)
    news = NewsDTO(
        link=article_preview_content.url,
        text=article.text,
        title=article.title,
        source='garant',
        timestamp=article_preview_content.timestamp,
        refers_to=article.refers_to,
    )
    logger.info(f"Распарсили новость: {news.link=}")
    return news


def parse_article_preview(article: Tag) -> ArticlePreviewContent:
    url = article.select_one('a.title').attrs['href']
    timestamp = dateparser.parse(
        article.select_one('time').contents[0],
        languages=['ru'],
    )
    return ArticlePreviewContent(
        url=prepare_url(url),
        timestamp=timestamp,
    )


def prepare_url(url: str) -> str:
    if url.startswith('http'):
        return url
    return GARANT_INDEX_URL + url


def get_id_in_url(url: str) -> str:
    if url.endswith('/'):
        url = url[:-1]
    return url.split('/')[-1]


def parse_article(article_url: str) -> ArticleContent:
    time.sleep(TIMEOUT)
    response = requests.get(article_url, headers=HEADERS)
    article = BeautifulSoup(response.text, features="html.parser")
    content = article.select_one('.page-content')
    title = content.select_one('h1').text
    body = content.select_one('.js-mediator-article').text
    refers_to = [
        prepare_url(a.attrs['href'])
        for a in content.select('a')
        if 'href' in a.attrs
    ]
    return ArticleContent(
        title=title,
        text=body,
        refers_to=refers_to,
    )
