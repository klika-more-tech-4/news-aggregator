import argparse
import asyncio
from asyncio import new_event_loop
from pathlib import Path
from typing import List
from urllib.parse import urljoin

import backoff
import httpx
import pytz
from bs4 import BeautifulSoup, SoupStrainer
from httpx import AsyncClient, HTTPError
from pydantic import BaseModel

import datetime as dt

from entities.news import NewsDTO


class VCLink(BaseModel):
    link: str
    content_id: int
    publish_date: int

    @property
    def publish_date_datetime(self) -> dt.datetime:
        return dt.datetime.fromtimestamp(self.publish_date, dt.timezone.utc).astimezone(pytz.timezone('Europe/Moscow')).replace(tzinfo=None)


class VCLinkList(BaseModel):
    __root__: List[VCLink]


class VCPost(BaseModel):
    title: str
    body: str
    hrefs: List[str]


def make_client() -> AsyncClient:
    return AsyncClient(
        # base_url='',
        headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'},
        follow_redirects=True
    )


async def fetch_initial_data(client: AsyncClient) -> str:
    res = await client.get('https://vc.ru/tag/новости')
    return res.text


@backoff.on_exception(backoff.expo, (HTTPError,), max_tries=30)
async def fetch_next_data(client: AsyncClient, link: VCLink, page: int) -> str:
    res = await client.get('https://vc.ru/tag/новости/default/more', params={
        'last_id': link.content_id,
        'page': page,
        'last_sorting_value': link.publish_date,
        'mode': 'raw',
        'exclude_ids': '[]'
    })
    return res.json()['data']['items_html']


def extract_links(data: str) -> VCLinkList:
    soup = BeautifulSoup(data, 'html.parser')
    feeds = soup.findAll('div', {'class': 'content-feed'})
    outs = []
    for feed in feeds:
        content_id = int(feed['data-content-id'])
        publish_date = int(feed['data-publish-date'])
        link = feed.find('a', {'class': 'content-link'})['href']
        outs.append(VCLink(content_id=content_id, publish_date=publish_date, link=link))
    return VCLinkList(__root__=outs)


@backoff.on_exception(backoff.expo, (HTTPError,), max_tries=30)
async def fetch_post_data(client: AsyncClient, link: str):
    dat = await client.get(link)
    return dat.text


def extract_post_data(link: VCLink, data: str) -> VCPost:
    soup = BeautifulSoup(data, 'html.parser')
    title = soup.find('h1', {'class': 'content-title'}).get_text().strip()
    body = soup.find('div', {'class': 'content--full'})
    for itm in body.find_all("div", {'class': 'content-info'}):
        itm.decompose()
    body_str = str(body)
    hrefs = [urljoin(link.link, x['href']) for x in body.findAll('a')]
    hrefs = [x for x in hrefs if '.' in x]
    return VCPost(
        title=title,
        body=body_str,
        hrefs=hrefs
    )


async def main():
    out_dir = Path('data') / 'vcru'
    out_dir.mkdir(parents=True, exist_ok=True)
    # links_dir = out_dir / 'links'
    # links_dir.mkdir(parents=True, exist_ok=True)

    client = make_client()
    data = await fetch_initial_data(client)
    links = extract_links(data)
    page = 1
    while len(links.__root__) > 0:
        last_link = links.__root__[-1]
        print(f'Last fetch: {last_link.publish_date_datetime}')
        post_strs = await asyncio.gather(*(fetch_post_data(client, lnk.link) for lnk in links.__root__))
        for link, post_str in zip(links.__root__, post_strs):
            try:
                post = extract_post_data(link, post_str)
                news_dto = NewsDTO(
                    link=link.link,
                    text=post.body,
                    title=post.title,
                    source='vc.ru',
                    timestamp=link.publish_date_datetime,
                    refers_to=post.hrefs
                )
                with (out_dir / f'{link.content_id}.json').open('w') as f:
                    f.write(news_dto.json(ensure_ascii=False))
            except:
                print(f'oh shit {link.link}')
        page += 1
        data = await fetch_next_data(client, last_link, page)
        links = extract_links(data)

    print()


if __name__ == '__main__':
    loop = new_event_loop()
    loop.run_until_complete(main())
