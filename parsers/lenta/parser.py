# Импорт библиотек
import backoff
import requests as rq
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import datetime
from urllib.parse import urljoin


class lentaRu_parser:
    def __init__(self):
        pass

    def _get_url(self, param_dict: dict) -> str:
        """
        Возвращает URL для запроса json таблицы со статьями

        url = 'https://lenta.ru/search/v2/process?'\
        + 'from=0&'\                       # Смещение
        + 'size=1000&'\                    # Кол-во статей
        + 'sort=2&'\                       # Сортировка по дате (2), по релевантности (1)
        + 'title_only=0&'\                 # Точная фраза в заголовке
        + 'domain=1&'\                     # ??
        + 'modified%2Cformat=yyyy-MM-dd&'\ # Формат даты
        + 'type=1&'\                       # Материалы. Все материалы (0). Новость (1)
        + 'bloc=4&'\                       # Рубрика. Экономика (4). Все рубрики (0)
        + 'modified%2Cfrom=2020-01-01&'\
        + 'modified%2Cto=2020-11-01&'\
        + 'query='                         # Поисковой запрос
        """
        hasType = int(param_dict['type']) != 0
        hasBloc = int(param_dict['bloc']) != 0

        url = 'https://lenta.ru/search/v2/process?' \
              + 'from={}&'.format(param_dict['from']) \
              + 'size={}&'.format(param_dict['size']) \
              + 'sort={}&'.format(param_dict['sort']) \
              + 'title_only={}&'.format(param_dict['title_only']) \
              + 'domain={}&'.format(param_dict['domain']) \
              + 'modified%2Cformat=yyyy-MM-dd&' \
              + 'type={}&'.format(param_dict['type']) * hasType \
              + 'bloc={}&'.format(param_dict['bloc']) * hasBloc \
              + 'modified%2Cfrom={}&'.format(param_dict['dateFrom']) \
              + 'modified%2Cto={}&'.format(param_dict['dateTo']) \
              + 'query={}'.format(param_dict['query'])

        return url

    @backoff.on_exception(backoff.expo, (Exception,), max_tries=10)
    def _get_search_table(self, param_dict: dict) -> pd.DataFrame:
        """
        Возвращает pd.DataFrame со списком статей
        """
        url = self._get_url(param_dict)
        r = rq.get(url)
        search_table = pd.DataFrame(r.json()['matches'])
        refers_to = []
        for link in search_table.url:
            soup = bs(rq.get(link).text, features="lxml").find_all('a', href=True)
            external = [soup_part['href'] for soup_part in soup] if soup else []
            hrefs = [urljoin('https://lenta.ru/', external_link) for external_link in external]
            hrefs = [x for x in hrefs if '.' in x]
            refers_to.append(str(hrefs))
        search_table['refers_to'] = refers_to
        return search_table


# Задаем тут параметры
use_parser = "LentaRu"

query = ''
offset = 0
size = 1000
sort = "3"
title_only = "0"
domain = "1"
material = "0"
bloc = "4"
dateFrom = '2015-01-01'
dateTo = "2022-10-10"

param_dict = {'query'     : query,
              'from'      : str(offset),
              'size'      : str(size),
              'dateFrom'  : dateFrom,
              'dateTo'    : dateTo,
              'sort'      : sort,
              'title_only': title_only,
              'type'      : material,
              'bloc'      : bloc,
              'domain'    : domain}

current_date = datetime.date(2020, 7, 25)
parser = lentaRu_parser()

while current_date <= datetime.date.today():
    param_dict[dateFrom] = current_date.strftime("%Y-%m-%d")
    param_dict[dateTo] = (current_date + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    lenna = 100
    part = 0
    tbl = parser._get_search_table(param_dict)
    tbl.to_csv(f"from_{current_date.strftime('%Y-%m-%d')}.csv")
    print(lenna, current_date)
    current_date += datetime.timedelta(days=1)




print(use_parser, "- param_dict:", param_dict)
