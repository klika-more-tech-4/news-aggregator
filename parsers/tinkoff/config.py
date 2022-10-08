from typing import Optional

BASE_URL = "https://www.tinkoff.ru/api/invest-gw/social/v1/profile/25cf055b-1543-47a8-b22e-4aa51b124f7b/post?limit=100&appName=socialweb&appVersion=1.29.0&origin=web&platform=web"
SESSION_ID = "VDR4XkoEyM7xtPAuYoT4FBYneHBPE46W.m1-prod-api"
SOURCE = "TINKOFF"


def generate_url(cursor: Optional[str]) -> str:
    additional_url = BASE_URL + f"&sessionId={SESSION_ID}"
    if cursor:
        additional_url = additional_url + f"&cursor={cursor}"
    return additional_url


def generate_post_url(id: str) -> str:
    return f"https://www.tinkoff.ru/api/invest-gw/social/v1/post/{id}?sessionId={SESSION_ID}&appName=socialweb&appVersion=1.29.0&origin=web&platform=web"
