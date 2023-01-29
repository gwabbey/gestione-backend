from sqlalchemy.orm import Session

from . import models, schemas


def get_table(db: Session, user_id: int, message: str):
    return db.query(models.User).filter(models.User.id == user_id, models.User.message == message).first()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_message(db: Session, message: str):
    return db.query(models.User).filter(models.User.message == message).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(name=user.name, message=user.message)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
