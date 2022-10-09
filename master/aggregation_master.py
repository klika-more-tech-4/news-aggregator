import json
from enum import Enum
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from data_collector.news_container import load_news
import datetime as dt

from ml.config import BASE_MODEL
from ml.get_future_prognose import FutureDigest
from ml.matching import NewsAggregator
from ml.okved_match.client import OkvedMatcher
from ml.vectorization import BertVectorizer
from utils.related_okveds import get_related


class NewsFilterType(str, Enum):
    all = 'all'
    my_okveds = 'my_okveds'
    my_and_contractor_okveds = 'my_and_contractor_okveds'


class UserRole(str, Enum):
    booker = 'booker'
    entrepreneur = 'entrepreneur'


class AggregationMaster:
    def __init__(self):
        self._news = load_news()
        self._bert = BertVectorizer(BASE_MODEL)
        self._news_aggregator = NewsAggregator()
        self._fut_dig = FutureDigest(self._news, self._bert, self._news_aggregator)
        with (Path(__file__).parent.parent / 'add_data' / 'source_mapping.json').open('r') as f:
            self._role_config = json.load(f)

    def _get_news_for(self, date_at: dt.datetime, user_role: UserRole, filter_type: NewsFilterType,
                      okveds: Optional[List[str]], period: int, return_dig_top: Optional[int]):
        if filter_type != NewsFilterType.all:
            if okveds is None or len(okveds) == 0:
                raise ValueError('empty okveds')
            okveds = set('.'.join(x.split('.')[:2]) for x in okveds)
            if filter_type == NewsFilterType.my_and_contractor_okveds:
                for x in okveds.copy():
                    rel = get_related(x)
                    if rel is not None:
                        okveds.update(rel)
                okveds.update(self._role_config[user_role]['add_okveds'])
        news = self._news[
            (self._news['timestamp'] >= date_at - dt.timedelta(days=period)) &
            (self._news['timestamp'] <= date_at) &
            (self._news['source'].isin(self._role_config[user_role]['sources']))
            ].reset_index(drop=True)
        # news['okveds'] = set()
        news_vectors = self._bert.vectorize(news['title'].tolist(), batch_size=32)
        if filter_type != NewsFilterType.all and len(okveds) > 0 and okveds is not None:
            digest = self._news_aggregator.get_personalized_trends(news, news_vectors, 1, user_okveds=okveds)
        else:
            digest = self._news_aggregator.get_trends(news, news_vectors, 1)
        digest_rank = []
        for k, dig in digest.items():
            date_len = (dig['timestamp'].max() - dig['timestamp'].min()) / np.timedelta64(1, 'D') if len(dig) > 1 else 0
            rank = (len(dig), date_len, k)
            digest_rank.append(rank)
        if return_dig_top is not None:
            digest_rank.sort(reverse=True)
            digest_rank = digest_rank[:return_dig_top]
        out_dig = []
        for dig_rank in digest_rank:
            dig_id = dig_rank[-1]
            dig = digest[dig_id].set_index('id', drop=True)
            out_dig.append(dig)
        return out_dig

    def create_digest(self, date_at: dt.datetime, user_role: UserRole, filter_type: NewsFilterType,
                      okveds: Optional[List[str]], ):
        digest = self._get_news_for(date_at, user_role, filter_type, okveds, period=7, return_dig_top=3)
        digest = [x[x['is_central_news']].iloc[0].to_dict() for x in digest]
        return digest

    def create_insights(self, date_at: dt.datetime, user_role: UserRole, filter_type: NewsFilterType,
                        okveds: Optional[List[str]]):
        digest = self._get_news_for(date_at, user_role, filter_type, okveds, period=7, return_dig_top=3)
        digest = pd.concat(digest)
        insights = self._fut_dig.get_future_digest(date_at, digest)
        return insights

    def create_trends(self, date_at: dt.datetime, user_role: UserRole, filter_type: NewsFilterType,
                      okveds: Optional[List[str]]):
        digest = self._get_news_for(date_at, user_role, filter_type, okveds, period=60, return_dig_top=3)
        # digest = NewsAggregator.rank_newsgroups(digest, 'square', 3)
        digest = [x[x['is_central_news']].iloc[0].to_dict() for x in digest]
        return digest


if __name__ == '__main__':
    master = AggregationMaster()
    # print(master._fut_dig.get_future_digest([1, 2, 3]))
    # pass
    params = {
        'date_at': dt.datetime.now() - dt.timedelta(days=7),
        'user_role': UserRole.entrepreneur,
        'filter_type': NewsFilterType.my_and_contractor_okveds,
        'okveds': ['28.3', '69.20']
    }
    # print(master.create_digest(**params))
    # # print(master.create_trends(**params))
    print(master.create_insights(**params))
    # pass
