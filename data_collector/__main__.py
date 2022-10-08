import copy
import datetime
import json
from pathlib import Path

from bs4 import BeautifulSoup
from textnorm import normalize_unicode, normalize_space
from tqdm.auto import tqdm
from urllib.parse import urljoin
import pandas as pd


def process_json(j):
    j = copy.deepcopy(j)
    s = BeautifulSoup(j['text'], 'html.parser')
    txt = s.get_text()
    txt = normalize_space(txt)
    txt = normalize_unicode(txt)
    j['text'] = txt
    ttl = j['title']
    ttl = normalize_space(ttl)
    ttl = normalize_unicode(ttl)
    j['title'] = ttl
    j['refers_to'] = [urljoin(j['link'], x) for x in j['refers_to']]
    j['timestamp'] = datetime.datetime.fromisoformat(j['timestamp'])
    return j


if __name__ == '__main__':

    root = Path('.')
    files = list(root.rglob('*.json*'))
    jsons = []
    for file in tqdm(files):
        with file.open('r') as f:
            if file.suffix == '.jsonl':
                jsons.extend([process_json(json.loads(x)) for x in tqdm(f.readlines())])
            else:
                dat = json.load(f)
                keys = list(dat.keys())
                if len(keys) == 1:
                    dat = dat[keys[0]]
                    jsons.extend([process_json(x) for x in dat])
                else:
                    jsons.append(process_json(dat))
    df = pd.DataFrame(jsons)
    df['id'] = df.index
    df['timestamp'] = pd.to_datetime(df['timestamp'].apply(lambda x: max(x, datetime.datetime(1970, 1, 1))))
    df['timestamp'] = df['timestamp'].apply(lambda x: x.isoformat())
    df.to_json(Path(__file__).parent.parent / 'add_data' / 'news.jsonl', lines=True, orient='records', force_ascii=False)


