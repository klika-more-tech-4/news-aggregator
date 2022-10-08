import json
from pathlib import Path

from data_collector.news_container import load_news
from ml.config import BASE_MODEL
from ml.vectorization import BertVectorizer
from vector_lookup.faiss_client import FaissClient, get_suggested_nlist, get_suggested_nprobe

if __name__ == '__main__':
    news = load_news()
    nlist = get_suggested_nlist(len(news))
    nprobe = get_suggested_nprobe(nlist)
    dims = 312
    db = FaissClient(gpu_num=-1, dims=dims, nlist=nlist, nprobe=nprobe)
    out_path = str(Path(__file__).parent.parent.parent / 'add_data' / 'news_index.ivf')
    vec = BertVectorizer(BASE_MODEL)
    vectors = vec.vectorize(news['title'].tolist(), batch_size=64)
    db.train_index(news['id'].to_numpy(), vectors, out_path)
    with (Path(__file__).parent.parent.parent / 'add_data' / 'news_index_params.json').open('w') as f:
        f.write(json.dumps({'nlist': nlist, 'nproba': nprobe, 'dims': dims}))
