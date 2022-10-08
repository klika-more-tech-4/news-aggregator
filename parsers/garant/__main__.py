import os
from tqdm import tqdm

from . import get_news


def main():
    os.makedirs('data', exist_ok=True)

    with open('data/garant.jsonl', 'w') as f:
        for _, news in tqdm(zip(range(15_000_000_000), get_news())):
            f.write(news.json(ensure_ascii=False) + '\n')


if __name__ == "__main__":
    main()
