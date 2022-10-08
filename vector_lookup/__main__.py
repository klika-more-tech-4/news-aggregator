import numpy as np
import pandas as pd

from ml.vectorization import BertVectorizer
from vector_lookup.faiss_client import FaissClient, get_suggested_nlist, get_suggested_nprobe

if __name__ == '__main__':
    lookup_num = 5
    lookup_at = 228

    vec = BertVectorizer('cointegrated/rubert-tiny2')
    texts = pd.read_pickle('outputs.pkl')['text'].tolist()
    n_sample = len(texts)
    print('Vectorizing')
    vectors = vec.vectorize(texts, batch_size=64)
    ids = np.arange(n_sample)
    nlist = get_suggested_nlist(n_sample)
    nprobe = get_suggested_nprobe(nlist)

    faiss = FaissClient(gpu_num=0, dims=312, nprobe=nprobe, nlist=nlist)
    print('Training index')
    faiss.train_index(ids, vectors, 'index.ivf')
    # or instead of training it could be faiss.load_index('index.ivf')
    print(f'Looking up {texts[lookup_at]}')
    neighbors = faiss.lookup_single(vectors[lookup_at], lookup_num)
    for idx, dist in neighbors:
        print(f'Distance={dist} Text={texts[idx]}')
    pass