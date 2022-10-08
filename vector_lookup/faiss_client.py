from math import sqrt
from typing import List, Tuple, Optional

import faiss
import numpy as np
from tqdm.auto import tqdm


def get_suggested_nlist(vector_count: int):
    return round(sqrt(vector_count))


def get_suggested_nprobe(nlist: int):
    return nlist // 4


class FaissClient:
    _index: faiss.IndexIVFFlat

    def __init__(self, gpu_num: int, dims: int, nlist: int, nprobe: int):
        self._gpu_num = gpu_num
        self._dims = dims
        self._nlist = nlist
        self._nprobe = nprobe

    def train_index(self, ids: np.ndarray, vectors: np.ndarray, out_file: str):
        quantizer = faiss.IndexFlatIP(self._dims)
        index = faiss.IndexIVFFlat(quantizer, self._dims, self._nlist)

        if self._gpu_num >= 0:
            index_ivf = faiss.extract_index_ivf(index)
            res = faiss.StandardGpuResources()
            idx = faiss.IndexFlatIP(self._dims)
            index_ivf.clustering_index = faiss.index_cpu_to_gpu(res, self._gpu_num, idx)
        index.nprobe = self._nprobe

        index.train(vectors)
        index.add_with_ids(vectors, ids=ids)
        faiss.write_index(index, out_file)
        self._index = index

    def load_index(self, index_file: str):
        index = faiss.read_index(index_file)
        index.nprobe = self._nprobe
        self._index = index

    def lookup_many(self, vectors: np.ndarray, n_neighbours: int) -> Tuple[np.ndarray, np.ndarray]:
        D, I = self._index.search(vectors, n_neighbours)
        return I, D

    def lookup_single(self, vector: np.ndarray, n_neighbours: int) -> List[Tuple[int, float]]:
        I, D = self.lookup_many(np.expand_dims(vector, 0), n_neighbours + 1)
        I, D = I.squeeze(0), D.squeeze(0)
        return [x for x in zip(list(I), list(D)) if x[1] != 0]
