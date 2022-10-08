from numpy import ndarray
from pandas import DataFrame
from sklearn.neighbors import NearestNeighbors

from clustering import Clusterer

from typing import Dict


def get_digest(news: DataFrame, embeddings: ndarray, min_samples_in_group: int) -> Dict[int, DataFrame]:
    data = news.copy()

    groups_label, central_news_idx = match_news(embeddings)
    data["group"] = groups_label
    data["is_central_news"] = False
    data.loc[central_news_idx, "is_central_news"] = True

    groups = {}
    for group_label, group in data.groupby("group"):
        if len(group) >= min_samples_in_group:
            groups[group_label] = group

    return groups


def match_news(embeddings: ndarray) -> [ndarray, ndarray]:
    clusterer = Clusterer("agglomerative")

    groups_label = clusterer.fit_predict(embeddings)
    central_news = get_indexes_central_components(embeddings, clusterer.centroids)

    return groups_label, central_news


def get_indexes_central_components(embeddings: ndarray, centroids: ndarray) -> ndarray:
    neigh = NearestNeighbors(n_neighbors=1)
    neigh.fit(embeddings)

    indexes = neigh.kneighbors(centroids, return_distance=False)[:, 0]

    return indexes
