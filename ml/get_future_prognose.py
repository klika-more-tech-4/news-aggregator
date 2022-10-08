import datetime

import pandas as pd
from topics import TopicGetter
from news_lookup.client import *
from matching import NewsAggregator
from typing import List, Dict

SUIT_PATH = 'sources/refers.jsonl'
NEWS_PATH = '../app_data/news.jsonl'


class FutureDigest():
    def __init__(self, data: pd.DataFrame):
        self.topicpredictor = TopicGetter()
        self.predictions = {ref[0]: ref[1] for ref in
                            pd.read_json(SUIT_PATH, lines=True, orient='records').itertuples()}
        self.vectorizer = BertVectorizer(BASE_MODEL)
        self.news = data
        self.lookup = NewsLookup()
        self.clustering = NewsAggregator()

    def get_single_future_ids(self, new_url):
        if new_url in self.predictions:
            return self.predictions[new_url]
        return []

    def get_future_pool(self, new_url, depth=3):
        to_process = [new_url]
        processed = []
        while depth:
            processed += to_process
            next_level = []
            for i in to_process:
                next_level += self.get_single_future_ids(i)
            to_process = next_level
            depth -= 1
        return processed + to_process

    def get_close_in_past(self, digest_news: pd.DataFrame):
        near_news = lookup.lookup(digest_news['id'].to_numpy(),
                                  self.vectorizer.vectorize(digest_news['title'].tolist(), batch_size=64))
        close_future_ids = []
        for near in near_news:
            close_future_ids += near

        far_feature_news = []
        for newid in close_future_ids:
            far_feature_news += self.get_future_pool(newid)
        return far_feature_news

    def get_new_importance(self, new_id) -> int:
        new_timestamp = self.news.iloc[new_id]['timestamp']
        start_timestamp = new_timestamp - datetime.timedelta(days=3)
        last_timestamp = new_timestamp + datetime.timedelta(days=3)
        subdata = self.news[(self.news.timestamp >= start_timestamp) & (self.news.timestamp <= last_timestamp)]
        clusters = self.clustering.get_trends(subdata,
                                              self.vectorizer.vectorize(subdata['title'].tolist(), batch_size=64), 1)
        new_rate = 0
        for cluster in clusters.values():
            if new_id in set(cluster['id']):
                new_rate = len(cluster)
                break
        return new_rate

    def get_topic_tops(self, news_id_pool: List[int]):
        subdata = self.news.loc[news_id_pool, :]
        subdata['topics'] = self.topicpredictor.get_topics(subdata['title'])
        ans_d = {}
        for topic in self.topicpredictor.topics:
            if topic not in set(subdata.topics):
                ans_d[topic] = '-'
            else:
                suitable_id = \
                sorted([(newid, self.get_new_importance(newid)) for newid in subdata[subdata.topic == topic]],
                       key=lambda x: x[1])[-1]
                ans_d[topic] = subdata.iloc[suitable_id]['title']
        return ans_d

    def format_future_digest(self, new_dict: Dict[str, str]):
        report = ''
        for topic in self.topicpredictor.topics:
            report += f"**{topic}:**\nnew_dict[topic]\n\n"
        return report

    def get_future_digest(self, top_news_ids: List[int]):
        return self.format_future_digest(self.get_topic_tops(top_news_ids))



# EXAMPLE
print(FutureDigest(load_news()).get_future_digest([1, 2, 3]))



