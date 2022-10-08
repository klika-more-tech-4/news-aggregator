from pathlib import Path

import pandas as pd


def load_news() -> pd.DataFrame:
    news_path = Path(__file__).parent.parent / 'add_data' / 'news.jsonl'
    news = pd.read_json(news_path, orient='records', lines=True)
    return news
