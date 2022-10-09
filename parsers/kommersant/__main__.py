import argparse
import logging
import asyncio as aio
import datetime as dt

import pandas as pd

from . import Parser

logging.basicConfig(level=logging.INFO)


async def parse(parser: Parser, output_path: str, q: aio.Queue[dt.date]) -> None:
    with open(output_path, 'w') as f:
        while not q.empty():
            date = await q.get()
            async for news in parser.get_news_for_date(date):
                f.write(news.json(ensure_ascii=False) + '\n')


async def queue_spammer(start_date: dt.date, end_date: dt.date, q: aio.Queue[dt.date]) -> None:
    for day in pd.date_range(start_date, end_date, freq='D'):
        await q.put(day)


async def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--source', type=str, required=True)
    arg_parser.add_argument('--rubric', type=int, required=True)
    arg_parser.add_argument('--start-date', type=str, required=True)
    arg_parser.add_argument('--end-date', type=str, required=True)
    args = arg_parser.parse_args()
    source = args.source
    rubric = args.rubric
    start_date = dt.datetime.strptime(args.start_date, '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(args.end_date, '%Y-%m-%d').date()

    parser = Parser(rubric=rubric, source=source)
    q: aio.Queue[dt.date] = aio.Queue(maxsize=2 ** 20)
    tasks = [aio.create_task(queue_spammer(start_date, end_date, q))]
    for i in range(10):
        tasks.append(aio.create_task(parse(parser, f'data/{source}_{rubric}_{i}.jsonl', q)))
    await aio.gather(*tasks)
    # parser = Parser(rubric=4, source='test_comm')
    #
    # res = [
    #     news async for news in parser.get_news(dt.date(2019, 3, 6), dt.date(2019, 3, 6))
    # ]
    # pprint([news.link for news in res])
    # print(len(res))

if __name__ == "__main__":
    aio.run(main())
