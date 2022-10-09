import logging
import datetime as dt
from typing import AsyncIterator

import backoff
import dateparser
import pandas as pd
from pydantic import BaseModel, HttpUrl, ValidationError
from httpx import AsyncClient, HTTPError
from bs4 import BeautifulSoup
from bs4.element import Tag

from entities.news import NewsDTO

logger = logging.getLogger()

KOMMERSANT_HOSTNAME = 'www.kommersant.ru'
KOMMERSANT_INDEX_URL = f'https://{KOMMERSANT_HOSTNAME}'


class ArticleContent(BaseModel):
    title: str
    text: str
    timestamp: dt.datetime
    refers_to: list[HttpUrl]


class ArticlePreviewContent(BaseModel):
    id: str
    title: str
    url: HttpUrl
    timestamp: dt.datetime


# Ща будет очень мощный костыль, чтобы валидировать ссылки на новости
class Crutch(BaseModel):
    link: HttpUrl


class Parser:
    def __init__(self, rubric: int, source: str):
        self.rubric = rubric
        self.source = source
        self._client = self.make_client()

    @staticmethod
    def make_client() -> AsyncClient:
        return AsyncClient(
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'},
            follow_redirects=True
        )

    @backoff.on_exception(backoff.expo, (HTTPError,), max_tries=30)
    async def fetch_initial_page(self) -> Tag:
        response = await self._client.get(f'{KOMMERSANT_INDEX_URL}/rubric/{self.rubric}')
        return BeautifulSoup(response.text, features='html.parser')

    @backoff.on_exception(backoff.expo, (HTTPError,), max_tries=30)
    async def fetch_page_for_day(self, date: dt.date) -> Tag:
        response = await self._client.get(f'{KOMMERSANT_INDEX_URL}/rubric/{self.rubric}/{date:%Y-%m-%d}')
        return BeautifulSoup(response.text, features='html.parser')

    @backoff.on_exception(backoff.expo, (HTTPError,), max_tries=30)
    async def fetch_article(self, url: str) -> Tag:
        response = await self._client.get(url)
        return BeautifulSoup(response.text, features='html.parser')

    @backoff.on_exception(backoff.expo, (HTTPError,), max_tries=30)
    async def fetch_next_page(self, date: dt.date, idafter: str) -> dict:
        response = await self._client.get(
            f'{KOMMERSANT_INDEX_URL}/listpage/lazyloaddocs',
            params={
                'regionid': 77,
                'listtypeid': 1,
                'listid': self.rubric,
                'date': date.strftime('%d.%m.%Y'),
                'intervaltype': 1,
                'idafter': idafter,
            }
        )
        return response.json()

    async def get_news_for_date(self, day: dt.date) -> AsyncIterator[NewsDTO]:
        logger.info(f'Парсим {day:%Y-%m-%d}')
        has_next = False
        idafter = None
        soup = await self.fetch_page_for_day(day)
        for article_preview in soup.select('.rubric_lenta .rubric_lenta__item'):
            try:
                article_preview_content = await self.parse_article_preview(article_preview)
                article = await self.parse_article(article_preview_content.url)
                news = self.article_data_to_news(article, article_preview_content)
                yield news
                logger.debug(f'Распарсили новость: {news.title=}')
                has_next = True
                idafter = article_preview_content.id
            except Exception as e:
                logger.exception(f'Ошибка при парсинге новости: {e}', exc_info=True)
        while has_next:
            try:
                next_page = await self.fetch_next_page(day, idafter)
                has_next = next_page.get('HasNextPage', False)
                for article_data in next_page.get('Items', []):
                    try:
                        article_id = article_data.get('DocsID', '')
                        article_preview_content = ArticlePreviewContent(
                            id=article_id,
                            title=article_data.get('Title', ''),
                            url=f'{KOMMERSANT_INDEX_URL}/doc/{article_id}',
                            timestamp=dt.datetime.fromtimestamp(article_data.get('DateDoc', 0)),
                        )
                        article = await self.parse_article(article_preview_content.url)
                        news = self.article_data_to_news(article, article_preview_content)
                        yield news
                        logger.debug(f'Распарсили новость: {news.title=}')
                        idafter = article_preview_content.id
                    except Exception as e:
                        logger.exception(f'Ошибка при парсинге новости: {e}', exc_info=True)
            except Exception as e:
                logger.exception(f'Ошибка при получении следующей страницы: {e}', exc_info=True)
                has_next = False

    async def get_news(self, start_date: dt.date, end_date: dt.date) -> AsyncIterator[NewsDTO]:
        for day in pd.date_range(start_date, end_date, freq='D'):
            async for news in self.get_news_for_date(day):
                yield news

    def article_data_to_news(self, article: ArticleContent, article_preview: ArticlePreviewContent) -> NewsDTO:
        return NewsDTO(
            link=article_preview.url,
            title=article_preview.title,
            text=article.text,
            source=self.source,
            timestamp=article.timestamp,
            refers_to=article.refers_to,
        )

    async def parse_article_preview(self, article: Tag) -> ArticlePreviewContent:
        url = article.attrs['data-article-url']
        article_id = article.attrs['data-article-docsid']
        title = article.attrs['data-article-title']
        timestamp = dateparser.parse(
            article.select_one('p.rubric_lenta__item_tag').contents[0],
            languages=['ru'],
        )
        return ArticlePreviewContent(
            id=article_id,
            title=title,
            url=self.prepare_url(url),
            timestamp=timestamp,
        )

    async def parse_article(self, article_url: str) -> ArticleContent:
        article = await self.fetch_article(article_url)
        title = article.select_one('header h1').text
        timestamp = dateparser.parse(article.select_one('header time').attrs['datetime'])
        body = '\n'.join([p.text for p in article.select('.doc__text')])
        refers_to = []
        for link in article.select('.doc__text a'):
            try:
                url = self.prepare_url(link.attrs['href'])
                Crutch(link=url)
                refers_to.append(url)
            except (ValidationError, KeyError):
                pass
        return ArticleContent(
            title=title,
            text=body,
            timestamp=timestamp,
            refers_to=refers_to,
        )

    @staticmethod
    def prepare_url(url: str) -> str:
        if url.startswith('http') or url.startswith('mailto') or url.startswith('tel'):
            return url
        return KOMMERSANT_INDEX_URL + url
