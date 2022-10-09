import datetime

import line_profiler_pycharm
import pandas as pd

from ml.okved_match.client import OkvedMatcher
from .topics import TopicGetter
from .news_lookup.client import *
from .matching import NewsAggregator
from typing import List, Dict

SUIT_PATH = str(Path(__file__).parent.parent / 'add_data' / 'refers.jsonl')
NEWS_PATH = str(Path(__file__).parent.parent / 'add_data' / 'news.jsonl')


class FutureDigest():
    def __init__(self, data: pd.DataFrame, vectorizer: BertVectorizer, agg: NewsAggregator):
        self.topicpredictor = TopicGetter()
        self.predictions = {x['link']: x['suits'] for _, x in pd.read_json(SUIT_PATH, lines=True, orient='records').iterrows()}
        self.vectorizer = vectorizer
        self.news = data
        self.news_by_link = {x['link']: x['id'] for _, x in self.news.iterrows()}
        self.lookup = NewsLookup()
        self.clustering = agg

    def get_single_future_ids(self, new_url):
        if new_url in self.predictions:
            return self.predictions[new_url]
        return []

    def get_future_pool(self, new_url, depth=3):
        to_process = [new_url]
        processed = []
        while depth:
            next_level = []
            for i in to_process:
                next_level += self.get_single_future_ids(i)
            to_process = next_level
            processed += to_process
            depth -= 1
        return processed

    def get_close_in_past(self, digest_news: pd.DataFrame):
        near_news = self.lookup.lookup(digest_news.index.to_numpy(),
                                  self.vectorizer.vectorize(digest_news['title'].tolist(), batch_size=64))
        close_future_ids = []
        for near in near_news:
            close_future_ids += near

        far_feature_news = []
        for newid in close_future_ids:
            lnk = self.news.loc[newid]['link']
            far_feature_news += [x for x in self.get_future_pool(lnk) if x != lnk]
        return list(set(self.news_by_link[x] for x in far_feature_news))

    @line_profiler_pycharm.profile
    def get_new_importance(self, new_id) -> int:
        # new_timestamp = self.news.loc[new_id]['timestamp']
        # start_timestamp = new_timestamp - datetime.timedelta(days=3)
        # last_timestamp = new_timestamp + datetime.timedelta(days=3)
        # subdata = self.news[(self.news.timestamp >= start_timestamp) & (self.news.timestamp <= last_timestamp)]
        # clusters = self.clustering.get_trends(subdata,
        #                                       self.vectorizer.vectorize(subdata['title'].tolist(), batch_size=64), 1)
        # new_rate = 0
        # for cluster in clusters.values():
        #     if new_id in set(cluster['id']):
        #         new_rate = len(cluster)
        #         break
        # return new_rate
        return 1

    def get_topic_tops(self, timestamp_at: datetime.datetime, news_id_pool: List[int]):
        subdata = self.news.loc[news_id_pool, :]
        subdata = subdata[subdata['timestamp'] <= (timestamp_at - datetime.timedelta(days=30))]
        subdata['topics'] = self.topicpredictor.get_topics(subdata['title'])
        ans_d = {}
        for topic in self.topicpredictor.topics:
            if topic not in set(subdata.topics):
                ans_d[topic] = '-'
            else:
                suitable_id = \
                sorted([(dat['id'], self.get_new_importance(dat['id'])) for _, dat in subdata[subdata.topics == topic].iterrows()],
                       key=lambda x: x[1])[-1]
                ans_d[topic] = subdata.loc[suitable_id[0]]['title']
        return ans_d

    def format_future_digest(self, new_dict: Dict[str, str]):
        report = ''
        for topic in self.topicpredictor.topics:
            report += f"**{topic}:**\n{new_dict[topic]}\n\n" if new_dict[topic]!='-' else ''
        return report

    def get_future_digest(self, timestamp_at: datetime.datetime, top_news_df: pd.DataFrame):
        return self.format_future_digest(self.get_topic_tops(timestamp_at, self.get_close_in_past(top_news_df)))


