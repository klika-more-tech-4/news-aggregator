from numpy import ndarray
from sklearn.neighbors import NearestNeighbors

from config import BATCH_SIZE, USE_POOLING

from typing import List


def match_news(news: List[str], vectorizer, clusterer) -> List[int]:
    embeddings = vectorizer.vectorize(news, batch_size=BATCH_SIZE, use_pooling=USE_POOLING)
    groups = clusterer.fit_predict(embeddings)

    return groups


def get_indexes_central_components(embeddings: ndarray, centroids: ndarray) -> ndarray:
    neigh = NearestNeighbors(n_neighbors=1)
    neigh.fit(embeddings)

    indexes = neigh.kneighbors(centroids, return_distance=False)[:, 0]

    return indexes
