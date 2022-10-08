from numpy import ndarray, random
from pandas import DataFrame
from sklearn.neighbors import NearestNeighbors

from .clustering import Clusterer

from typing import Dict, List


class NewsAggregator:
    def __init__(self):
        self._clusterer = Clusterer("agglomerative")
        self._okved_matcher = None

    def get_personalized_trends(self, news: DataFrame,
                                embeddings: ndarray,
                                min_samples_in_group: int,
                                user_okveds: List,
                                min_match_rate: float = 0.5) -> Dict[int, DataFrame]:
        newsgroups = self._grouping_news(news, embeddings, min_samples_in_group)

        for group_label in list(newsgroups.keys()):
            okveds = self._okved_matcher.lookup(newsgroups[group_label]["id"])
            intersect = okveds["okveds"].apply(lambda s: self._find_intersection(s, user_okveds))
            match_rate = intersect.mean()

            if match_rate < min_match_rate:
                del newsgroups[group_label]

        return newsgroups

    def get_trends(self, news: DataFrame, embeddings: ndarray, min_samples_in_group: int) -> Dict[int, DataFrame]:
        return self._grouping_news(news, embeddings, min_samples_in_group)

    def _grouping_news(self, news: DataFrame, embeddings: ndarray, min_samples_in_group: int) -> Dict[int, DataFrame]:
        data = news.copy()

        groups_label, central_news_idx = self._match_news(embeddings)
        data["group"] = groups_label
        data["is_central_news"] = False
        data.loc[central_news_idx, "is_central_news"] = True

        groups = {}
        for group_label, group in data.groupby("group"):
            if len(group) >= min_samples_in_group:
                groups[group_label] = group

        return groups

    def _match_news(self, embeddings: ndarray) -> [ndarray, ndarray]:

        groups_label = self._clusterer.fit_predict(embeddings)
        central_news = self._get_indexes_central_components(embeddings)

        return groups_label, central_news

    def _get_indexes_central_components(self, embeddings: ndarray) -> ndarray:
        neigh = NearestNeighbors(n_neighbors=1)
        neigh.fit(embeddings)

        indexes = neigh.kneighbors(self._clusterer.centroids, return_distance=False)[:, 0]

        return indexes

    @staticmethod
    def _find_intersection(s, user_okveds):
        s = set(s)
        user_okveds = set(user_okveds)
        intersection = set(s).intersection(set(user_okveds))
        return True if len(intersection) > 0 else False
