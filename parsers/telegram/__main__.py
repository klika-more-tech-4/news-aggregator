from typing import List, Optional
from datetime import datetime
from asyncio import sleep

from pyrogram import client, types, enums
from pydantic import BaseModel, ValidationError

from settings import settings
from entities.news import NewsDTO


def message_to_dto(message: types.messages_and_media.message.Message) -> Optional[NewsDTO]:
    if message.text:
        title = message.text
        if message.entities:
            links = [
                entity.url
                for entity in message.entities
                if entity.type == enums.message_entity_type.MessageEntityType.TEXT_LINK
            ]
        else:
            links = []
    elif message.caption:
        title = message.caption
        if message.caption_entities:
            links = [
                entity.url
                for entity in message.caption_entities
                if entity.type == enums.message_entity_type.MessageEntityType.TEXT_LINK
            ]
        else:
            links = []
    else:
        return

    timestamp = message.date
    source = message.sender_chat.username
    link = f"https://t.me/{message.sender_chat.username}/{message.id}"

    return NewsDTO(
        link=link,
        text="",
        title=title,
        source=source,
        timestamp=timestamp,
        refers_to=links,
    )


async def main(chat_placeholder: str):
    async with client.Client(
        "my_account", settings.telegram_api_id, settings.telegram_api_hash, phone_number=settings.telegram_phone_number
    ) as app:
        counter = 0
        news = []
        async for message in app.get_chat_history(chat_placeholder):
            counter += 1
            try:
                if m := message_to_dto(message):
                    news.append(m)
            except ValidationError:
                pass
            if counter % 1000 == 0:
                print(counter)
                await sleep(10)
        print(len(news))
        return TempModel(telegram=news)


class TempModel(BaseModel):
    telegram: List[NewsDTO]
