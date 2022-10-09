import json
from pathlib import Path
from typing import List

import fasttext
import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from sklearn.preprocessing import normalize
from tqdm.auto import tqdm

from ml.config import BASE_MODEL
from ml.vectorization import BertVectorizer
from vector_lookup.faiss_client import FaissClient, get_suggested_nlist, get_suggested_nprobe

_keep = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя- '
nltk.download("stopwords")
_russian_stopwords = stopwords.words("russian")


def _process_texts(text):
    text = [''.join([x if x in _keep else ' ' for x in x.lower()]) for x in text]
    text = ' '.join(text)
    text = ' '.join([x for x in text.strip().split() if x not in _russian_stopwords])
    text = ' '.join(text.replace('-', ' ').split())
    return text


def okved_data_flatten(x: pd.Series):
    text = []
    text.append(x['SectionName'])
    text.append(x['Name'])
    if isinstance(x['Notes'], str):
        text.append(x['Notes'])
    text = _process_texts(text)
    # text_o = []
    # for x in text:
    #     if x not in text_o:
    #         text_o.append(x)
    return text


def news_data_flatten(x: pd.Series):
    title = x['title']
    text = x['text']
    return _process_texts([title, text])


class FastTextVectorizer():
    def __init__(self, model_path: str):
        self._model = fasttext.load_model(model_path)

    def vectorize(self, sentences: List[str]):
        vecs = [self._model.get_sentence_vector(sent) for sent in sentences]
        return normalize(np.stack(vecs), axis=1)

def get_okved_data(x: pd.Series):
    code = x["Kod"]
    name = f'{x["SectionName"].lower()} > {x["Name"].lower()}'
    return {'code': code, 'name': name}

if __name__ == '__main__':
    vectorizer = FastTextVectorizer(str(Path(__file__).parent.parent.parent / 'add_data' / 'cc.ru.300.bin'))

    okveds = pd.read_csv(Path(__file__).parent.parent.parent / 'add_data' / 'OKVED.csv')
    okved_ids = okveds.index.to_numpy()
    okved_texts = okveds.apply(okved_data_flatten, axis=1).tolist()
    # vectorizer = BertVectorizer(BASE_MODEL)
    okved_vectors = vectorizer.vectorize(okved_texts)
    nlist = get_suggested_nlist(len(okved_texts))
    nproba = get_suggested_nprobe(nlist)
    db = FaissClient(0, 300, nlist, nproba)
    db.train_index(okved_ids, okved_vectors, 'okved_index.ivf')

    news = pd.read_json(Path(__file__).parent.parent.parent / 'add_data' / 'news.jsonl', orient='records', lines=True)
    outputs = {}
    for news_batch in tqdm(np.array_split(news, len(news) // 200)):
        news_texts = news_batch.apply(news_data_flatten, axis=1).tolist()
        news_ids = news_batch.index.to_numpy()
        news_vectors = vectorizer.vectorize(news_texts)
        best_okved_idx, best_okved_dist = db.lookup_many(news_vectors, 100)
        best_okved_mask = best_okved_dist <= 0.62
        best_okved_mask[:, 0] = True
        best_okved_idx = [idx[msk] for msk, idx in zip(best_okved_mask, best_okved_idx)]
        best_okved = [okveds.iloc[x]['Kod'].tolist() for x in best_okved_idx]
        for idx, okv in zip(news_ids, best_okved):
            outputs[idx] = okv
    outputs = {int(k): list(set('.'.join(vv.split('.')[:2]) for vv in v)) for k, v in outputs.items()}
    with Path(Path(__file__).parent.parent.parent / 'add_data' / 'news_okved.json').open('w') as f:
        json.dump(outputs, f)
