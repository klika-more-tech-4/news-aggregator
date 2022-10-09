from numpy import ndarray, array, unique, mean
from sklearn.cluster import DBSCAN, Birch, AgglomerativeClustering

from copy import deepcopy
from typing import Dict, Union


class Clusterer:
    default_parameters = {
        "eps": 0.35,
        "min_samples": 2,
        "metric": "cosine",
        "threshold": 0.5,
        "branching_factor": 70,
        "n_clusters": None,
        "affinity": "cosine",
        "compute_full_tree": True,
        "linkage": "complete",
        "distance_threshold": 0.2
    }

    def __init__(self, method: str = "dbscan", parameters: Union[Dict, None] = None):
        self.method = method

        self.parameters = deepcopy(self.default_parameters)
        if parameters is not None:
            self.parameters.update(parameters)

        if method == "birch":
            self.model = Birch(threshold=self.parameters["threshold"],
                               branching_factor=self.parameters["branching_factor"],
                               n_clusters=self.parameters["n_clusters"])
        elif method == "agglomerative":
            self.model = AgglomerativeClustering(n_clusters=self.parameters["n_clusters"],
                                                 affinity=self.parameters["affinity"],
                                                 compute_full_tree=self.parameters["compute_full_tree"],
                                                 linkage=self.parameters["linkage"],
                                                 distance_threshold=self.parameters["distance_threshold"])

        else:
            self.model = DBSCAN(eps=self.parameters["eps"],
                                min_samples=self.parameters["min_samples"],
                                metric=self.parameters["metric"], )

        self.centroids = None

    def fit_predict(self, embeddings: ndarray) -> ndarray:
        labels = self.model.fit_predict(embeddings)
        self.centroids = self._get_centroids(embeddings, labels)
        return labels

    def _get_centroids(self, embeddings: ndarray, labels: ndarray) -> ndarray:
        if isinstance(self.model, Birch):
            return self.model.subcluster_centers_
        else:
            return self._calc_centroids_dbscan(embeddings, labels)

    @staticmethod
    def _calc_centroids_dbscan(embeddings: ndarray, labels: ndarray) -> ndarray:
        centroids = []
        for label in unique(labels):
            if label != -1:
                label_components = embeddings[labels == label]
                centroids.append(mean(label_components, axis=0))

        return array(centroids)
