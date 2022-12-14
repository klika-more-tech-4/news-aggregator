from typing import Any, List
from datetime import datetime

from pydantic import BaseModel

from parsers.bankiru.parser import parse_all


class TempModel(BaseModel):
    tinkoff: List[Any]


if __name__ == "__main__":
    parse_all(datetime(year=2022, month=6, day=23))
