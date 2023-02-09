from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal
from .models import Work, Operator


def get_users(db: Session):
    return db.query(models.Operator).order_by(models.Operator.id).all()


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


def get_table(db: Session, user_id: int, message: str):
    return db.query(models.Operator).filter(models.Operator.id == user_id, models.Operator.message == message).first()


def get_joined_tables():
    db = SessionLocal()
    result = db.query(Work, Operator).join(Operator, Work.operator_id == Operator.id).first()
    if result:
        return result
    return 'something went wrong'


def create_activity(db: Session, work: schemas.Work):
    db_work = models.Work(date=work.date, intervention_duration=work.intervention_duration,
                          intervention_type=work.intervention_type, intervention_location=work.intervention_location,
                          client=work.client, site=work.site, description=work.description, notes=work.notes,
                          trip_kms=work.trip_kms, cost=work.cost, operator_id=work.operator_id)
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work
