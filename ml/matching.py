from numpy import ndarray
from sklearn.neighbors import NearestNeighbors

from config import BATCH_SIZE, USE_POOLING

from typing import List, DefaultDict
from collections import defaultdict


def match_news(news: List[str], vectorizer, clusterer) -> DefaultDict[int, List[str]]:
    embeddings = vectorizer.vectorize(news, batch_size=BATCH_SIZE, use_pooling=USE_POOLING)
    labels = clusterer.fit_predict(embeddings)

    groups = defaultdict(list)
    for label, title in zip(labels, news):
        groups[label].append(title)

    return groups


def get_indexes_central_components(embeddings: ndarray, centroids: ndarray) -> ndarray:
    neigh = NearestNeighbors(n_neighbors=1)
    neigh.fit(embeddings)

    indexes = neigh.kneighbors(centroids, return_distance=False)[:, 0]

    return indexes
