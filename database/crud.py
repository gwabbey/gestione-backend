from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal
from .models import Work, Operator, Client


def get_users(db: Session):
    return db.query(models.Operator).all()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.Operator).filter(models.Operator.id == user_id).first()


def get_user_by_full_name(db: Session, first_name: str, last_name: str):
    return db.query(models.Operator).filter(models.Operator.first_name == first_name,
                                            models.Operator.last_name == last_name).first()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.Operator(first_name=user.first_name, last_name=user.last_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def add_client(db: Session, client: schemas.ClientCreate):
    db_client = models.Client(name=client.name)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def get_clients(db: Session):
    return db.query(models.Client).all()


def get_table(db: Session, user_id: int, message: str):
    return db.query(models.Operator).filter(models.Operator.id == user_id, models.Operator.message == message).first()


def get_joined_tables():
    db = SessionLocal()
    result = db.query(Work, Operator).join(Operator, Work.operator_id == Operator.operator_id).first()
    result2 = db.query(Work, Client).join(Client, Work.client == Client.name).first()
    if result and result2:
        return result, result2
    return 'something went wrong'
