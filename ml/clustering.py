from numpy import ndarray
from sklearn.cluster import DBSCAN, Birch

from copy import deepcopy
from typing import Dict, Union


class Clusterer:
    default_parameters = {
        "eps": 1.,
        "min_samples": 2,
        "threshold": 0.5,
        "branching_factor": 50,
        "n_clusters": None
    }

    def __init__(self, method: str = "dbscan", parameters: Union[Dict, None] = None):

        self.parameters = deepcopy(self.default_parameters)
        if parameters is not None:
            self.parameters.update(parameters)

        if method == "birch":
            self.model = Birch(threshold=self.parameters["threshold"],
                               branching_factor=self.parameters["branching_factor"],
                               n_clusters=self.parameters["n_clusters"])
        else:
            self.model = DBSCAN(eps=self.parameters["eps"],
                                min_samples=self.parameters["min_samples"])

    def fit_predict(self, embeddings: ndarray) -> ndarray:
        labels = self.model.fit_predict(embeddings)
        return labels
