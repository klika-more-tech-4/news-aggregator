from enum import Enum

from pydantic import BaseSettings


class Environment(str, Enum):
    dev = 'dev'
    prod = 'prod'


class Settings(BaseSettings):
    env: Environment = Environment.dev

    host: str = '0.0.0.0'
    port: int = 8000

    db_uri: str = 'sqlite:///db.sqlite'


settings = Settings(_env_file='.env', _env_file_encoding='utf-8')
