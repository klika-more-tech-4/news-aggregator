from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime
from tqdm import tqdm


class RbcParser():
    def __init__(self):
        pass

    def get_url(self, param_dict: Dict) -> str:
        url = "https://www.rbc.ru/v10/search/ajax?" + "&".join([f"{key}={param_dict[key]}" for key in param_dict])
        return url

    def get_text_from_new(self, url: str) -> Tuple[str, str]:
        response = requests.get(url)
        soup = bs(response.text, features="lxml")
        p_text = soup.find_all('p')

        links = []
        for article in p_text:
            url = article.find('a', href=True)
            if url:
                link = url['href']
                links.append(link)
        links = '\n'.join(links)

        text = ' '.join(map(lambda x:
                            x.text.replace('<br />', '\n').strip(),
                            p_text)) if p_text else None

        return text, links

    def standartise_new(self, new):
        return {'link': new['fronturl'],
                'text': new['text'],
                'title': new['title'],
                'source': 'RBC',
                'timestamp': datetime.fromtimestamp(new['publish_date_t']).isoformat(),
                'refers_to': new['links']
                }

    def get_news(self, param_dict: Dict) -> List[Dict[str, str]]:
        url = self.get_url(param_dict)
        print(url)
        response = requests.get(url)
        news = response.json()['items']
        for item in tqdm(news):
            item['text'], item['links'] = self.get_text_from_new(item['fronturl'])
        return [self.standartise_new(new) for new in news]


param_dict = {'query': 'РБК',
              'dateFrom': '01.07.2022',
              'dateTo': '22.07.2022'}

parser = RbcParser()
tbl = parser.get_news(param_dict)
print(len(tbl))
print(tbl[0]['title'])

param_dict = {'query': 'РБК',
              'dateFrom': '01.07.2022',
              'dateTo': '22.07.2022',
              'offset': 50,
              'limit': 50}

parser = RbcParser()
tbl = parser.get_news(param_dict)
print(len(tbl))
print(tbl[0]['title'])