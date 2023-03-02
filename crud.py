import datetime
from typing import Type

import models
import schemas
from database import SessionLocal, Base


def get_all_records(db: SessionLocal, model: Type[Base]):
    return db.query(model).order_by(model.id).all()


users = get_all_records(SessionLocal, models.User)
clients = get_all_records(SessionLocal, models.Client)
sites = get_all_records(SessionLocal, models.Site)
intervention_types = get_all_records(SessionLocal, models.InterventionType)


def get_works_by_user_id(db: SessionLocal, user_id: int):
    return db.query(models.Work).filter(models.Work.operator_id == user_id).order_by(
        models.Work.created_at.desc()).all()


def get_work_table(db: SessionLocal):
    result = db.query(models.Work, models.User).join(models.User, models.Work.operator_id == models.User.id).order_by(
        models.Work.id.desc()).all()
    if result:
        return result
    return 'something went wrong'


def get_user_by_id(db: SessionLocal, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: SessionLocal, user: schemas.UserCreate):
    db_user = models.User(first_name=user.first_name, last_name=user.last_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_activity(db: SessionLocal, work: schemas.Work, current_user: models.User):
    db_work = models.Work(date=work.date,
                          intervention_duration=work.intervention_duration,
                          intervention_type=work.intervention_type,
                          intervention_location=work.intervention_location,
                          client=work.client,
                          site=work.site,
                          description=work.description,
                          notes=work.notes,
                          trip_kms=work.trip_kms,
                          cost=work.cost,
                          operator_id=current_user.id,
                          created_at=datetime.datetime.utcnow())
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work
