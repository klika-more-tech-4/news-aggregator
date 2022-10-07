from datetime import datetime
from typing import List
import re

import requests
from bs4 import BeautifulSoup, SoupStrainer

from parsers.bankiru.config import generate_url_date


def parse_news_for_date(d: datetime) -> List[str]:
    ids = []
    link_re = re.compile("\/news\/lenta\/\?id=([0-9]{1,})")
    r = requests.get(generate_url_date(d))
    for link in BeautifulSoup(r.text, parse_only=SoupStrainer("a"), features="html.parser"):
        if link.has_attr("href"):
            try:
                ids.append(link_re.match(link["href"]).group(1))
            except:
                pass
    return list(set(ids))
