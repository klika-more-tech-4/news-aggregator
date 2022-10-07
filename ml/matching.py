from config import BATCH_SIZE, USE_POOLING

from typing import List


def match_news(news: List[str], vectorizer, clusterer) -> List[int]:
    embeddings = vectorizer.vectorize(news, batch_size=BATCH_SIZE, use_pooling=USE_POOLING)
    groups = clusterer.fit_predict(embeddings)

    return groups
