from pydantic import BaseSettings


class Settings(BaseSettings):
    db_uri: str = 'sqlite:///db.sqlite'


settings = Settings()
