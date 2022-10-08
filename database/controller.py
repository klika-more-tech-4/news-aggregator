from sqlmodel import Session, select
from database import TelegramUserModel, engine


def get_user(user_id: str | int) -> TelegramUserModel:
    with Session(engine) as session:
        user = session.query(TelegramUserModel).filter(TelegramUserModel.id == str(user_id)).one_or_none()
        if user is None:
            user = TelegramUserModel(id=str(user_id), state="NEW")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def set_user(user: TelegramUserModel):
    with Session(engine) as session:
        session.merge(user)
        session.commit()
