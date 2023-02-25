import models
from sqlalchemy.orm import Session


def get_user(db, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_works_by_user_id(db: Session, user_id: int):
    return db.query(models.Work).filter(models.Work.operator_id == user_id).all()
