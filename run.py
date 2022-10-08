import uvicorn

from api import app
from settings import settings


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )
