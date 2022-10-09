import json
from pathlib import Path

import pandas as pd


class OkvedMatcher:
    def __init__(self):
        with open(Path(__file__).parent.parent.parent / 'add_data' / 'news_okved.json') as f:
            self._okveds = json.load(f)
            self._okveds = {int(k): v for k, v in self._okveds.items()}

    def lookup(self, data: pd.DataFrame):
        dat = [self._okveds[idx] for idx in data['id']]
        return pd.DataFrame({'id': data['id'], 'okveds': dat})


if __name__ == '__main__':
    mp = OkvedMatcher()
    outs = mp.lookup(pd.DataFrame({'id': [123, 228, 1337]}))
    print(outs)