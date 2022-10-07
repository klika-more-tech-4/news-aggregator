import argparse
import asyncio
from asyncio import new_event_loop
from pathlib import Path
from typing import List
from urllib.parse import urljoin

import pandas as pd
import pytz
from bs4 import BeautifulSoup, SoupStrainer
from httpx import AsyncClient
from pydantic import BaseModel

import datetime as dt

from tqdm.auto import tqdm

from entities.news import NewsDTO


def make_client() -> AsyncClient:
    return AsyncClient(
        # base_url='',
        headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
            # shitton
            'Cookie': "ASE_PHPSESSID=shimgp8hd5873ov7qc3nntj410; ASE_windowFirstViewDate=2022-10-07%2022%3A41%3A05; tmr_lvid=eea93ed8d344367decd68bcbb1a00fe6; tmr_lvidTS=1665171666647; _ym_uid=1665171667384525201; _ym_d=1665171667; _ym_isad=2; __utma=134473591.1433194845.1665171667.1665171667.1665171667.1; __utmc=134473591; __utmz=134473591.1665171667.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmb=134473591.1.10.1665171667; _ga_3S9RDYN8D2=GS1.1.1665171666.1.0.1665171666.60.0.0; _ga=GA1.1.344271988.1665171667; __gads=ID=bf225760214455f0-220490713cce000b:T=1665171666:RT=1665171666:S=ALNI_MbxXXIXg1b82BCxhlY3TT0IRHps9w; __gpi=UID=0000087e6d5ea1cd:T=1665171666:RT=1665171666:S=ALNI_MbpI1_OtyZqGHI_RYtW0NI3ju2h6Q; singularToken=8293b651-380b-c095-cc73-742a5fb376a9; amnesty=robinSameSite; robin=ef71c2078e204df8a26f929edd87d9f3a031e9acff1a4c21ae93119124437c11; deadpool=81029e0b-576e-4677-8480-1aea20e4da41; tmr_reqNum=6; ASE_anonymousId=e180e97b480aba2cd6f6c885fecc5893; ASE_userLastVisit=2022-10-07%2022%3A41%3A08"
        },
        follow_redirects=True,
        # cookies={
        #     'ASE_anonymousId': 'e180e97b480aba2cd6f6c885fecc5893',
        #     'ASE_userLastVisit': '2022-10-07%2022%3A41%3A08',
        #     # ''
        # }
    )


async def fetch_date(client: AsyncClient, date: dt.date) -> str:
    res = await client.get(f'https://www.business.ru/news/date/{date.strftime("%Y%m%d")}')
    return res.text


def extract_date_links(data: str) -> List[str]:
    soup = BeautifulSoup(data, 'html.parser')
    links = soup.find_all('a', {'class': 'defaultBlock__itemTitleLink'})
    return [urljoin('https://www.business.ru/news/', x['href']) for x in links]


async def fetch_post(client: AsyncClient, link: str):
    res = await client.get(link)
    return res.text


def extract_post_data(link: str, post: str) -> NewsDTO:
    soup = BeautifulSoup(post, 'html.parser')
    title = soup.find('h1', {'class': 'page__title'}).get_text().strip()
    container = soup.find_all('div', {'class': 'news-content'})[-1]
    for div in container.find_all('div'):
        div.decompose()
    hrefs = [urljoin(link, x['href']) for x in container.find_all('a')]
    hrefs = [x for x in hrefs if '.' in hrefs]
    date_time = dt.datetime.strptime(soup.find('meta', {'itemprop': 'dateModified'})['content'], '%Y-%m-%d %H:%M:%S')
    return NewsDTO(
        link=link,
        text=str(container),
        title=title,
        source='business.ru',
        timestamp=date_time,
        refers_to=hrefs
    )


async def main():
    out_dir = Path('data') / 'businessru'
    out_dir.mkdir(parents=True, exist_ok=True)

    client = make_client()
    dates = list(pd.date_range(dt.date(2015, 8, 3), dt.date.today())[::-1])
    for date in tqdm(dates):
        date_links = await fetch_date(client, date)
        date_links = extract_date_links(date_links)
        post_strs = await asyncio.gather(*(fetch_post(client, lnk) for lnk in date_links))
        for i, (link, post) in enumerate(zip(date_links, post_strs)):
            try:
                post_data = extract_post_data(link, post)
                with (out_dir / f'{date}_{i}.json').open('w') as f:
                    f.write(post_data.json(ensure_ascii=False))
            except:
                print(f'oh shit {link}')


if __name__ == '__main__':
    loop = new_event_loop()
    loop.run_until_complete(main())
