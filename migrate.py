from pathlib import Path

import pandas as pd

if __name__ == '__main__':
    news = pd.read_json(Path(__file__).parent / 'add_data' / 'news.jsonl', orient='records', lines=True)
    news['id'] = news.index
    pass