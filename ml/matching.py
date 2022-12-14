import line_profiler_pycharm
from numpy import ndarray
from pandas import DataFrame, Series
from sklearn.neighbors import NearestNeighbors

from .clustering import Clusterer
from .okved_match.client import OkvedMatcher

from typing import Dict, List, Union


class NewsAggregator:
    def __init__(self):
        self._clusterer = Clusterer("agglomerative")
        self._okved_matcher = OkvedMatcher()

    @line_profiler_pycharm.profile
    def get_personalized_trends(self, news: DataFrame,
                                embeddings: ndarray,
                                min_samples_in_group: int,
                                user_okveds: List,
                                min_match_rate: float = 0.5) -> Dict[int, DataFrame]:
        def _find_intersection(news_okveds: List[str], usr_okveds: List[str]):
            news_okveds = news_okveds + self._cut_okveds(news_okveds)
            intersection = set(usr_okveds).intersection(set(news_okveds))
            return True if len(intersection) > 0 else False

        newsgroups = self._grouping_news(news, embeddings, min_samples_in_group)

        for group_label in list(newsgroups.keys()):
            okveds = self._okved_matcher.lookup(newsgroups[group_label])
            intersect = okveds["okveds"].apply(lambda s: _find_intersection(s, user_okveds))
            match_rate = intersect.mean()

            if match_rate < min_match_rate:
                del newsgroups[group_label]

        return newsgroups

    def get_trends(self, news: DataFrame, embeddings: ndarray, min_samples_in_group: int) -> Dict[int, DataFrame]:
        return self._grouping_news(news, embeddings, min_samples_in_group)

    @staticmethod
    def rank_newsgroups(news_group: Dict[int, DataFrame], by: str = "square", top_n: int = 3) -> Dict[int, DataFrame]:
        """
        by: one of the ["square", "power"]
        """
        assert by in ["square", "power"], "the parameter 'by' must be one of (square, power)"
        group_metrics = []

        for group_label in news_group:
            group = news_group[group_label]

            diff_timestamp = group["timestamp"].max() - group["timestamp"].min()
            len_group = diff_timestamp.days
            power_group = len(group)

            if by == "square":
                group_metrics.append((len_group / power_group, group_label, group))
            else:
                group_metrics.append((power_group, group_label, group))

        top_news_groups = sorted(group_metrics, key=lambda x: x[0], reverse=True)[:top_n]

        return {group_label: group for _, group_label, group in top_news_groups}

    def _grouping_news(self, news: DataFrame, embeddings: ndarray, min_samples_in_group: int) -> Dict[int, DataFrame]:
        data = news.copy().reset_index(drop=True)

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

    def _cut_okveds(self, all_okveds: List, levels_kept: int = 1) -> List:
        return [self._cut_okved(okved, part_to=levels_kept) for okved in all_okveds]

    @staticmethod
    def _cut_okved(okved_code: Union[str, float], part_to: int, part_from: int = 0) -> str:
        okved_code_parts = str(okved_code).split(".")
        return ".".join(okved_code_parts[part_from:part_to])
