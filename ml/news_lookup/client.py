import json
from pathlib import Path
from typing import List

import numpy as np

from data_collector.news_container import load_news
from ml.config import BASE_MODEL
from ml.vectorization import BertVectorizer
from vector_lookup.faiss_client import FaissClient


class NewsLookup:
    def __init__(self, dist_threshold=0.35, lookup_n=100):
        add_data = Path(__file__).parent.parent.parent / 'add_data'
        with (add_data / 'news_index_params.json').open('r') as f:
            faiss_params = json.load(f)
        self._faiss = FaissClient(-1, faiss_params["dims"], faiss_params['nlist'], faiss_params['nproba'])
        self._faiss.load_index(str(add_data / 'news_index.ivf'))
        self._dist_threshold = dist_threshold
        self._lookup_n = lookup_n

    def lookup(self, news_ids: np.ndarray, news_vectors: np.ndarray) -> List[List[int]]:
        idxs, dists = self._faiss.lookup_many(news_vectors, self._lookup_n)
        # idxs = [found[found != orig] for found, orig in zip(idxs, news_ids)]
        outputs = []
        for found, dist, orig in zip(idxs, dists, news_ids):
            mask = (found != orig) & (dist < self._dist_threshold)
            outs = found[mask]
            outputs.append(outs.tolist())
        return outputs


if __name__ == '__main__':
    vectorizer = BertVectorizer(BASE_MODEL)
    news = load_news()
    lookup = NewsLookup()
    s = news.sample(10)
    near_news = lookup.lookup(s['id'].to_numpy(), vectorizer.vectorize(s['title'].tolist(), batch_size=64))
    for near, (_, orig) in zip(near_news, s.iterrows()):
        print(orig['title'], 'опубликована', orig['timestamp'])
        print('NEAR:')
        for n in near:
            nn = news.iloc[n]
            print(nn['title'], 'опубликована', nn['timestamp'])
        print('========================')
