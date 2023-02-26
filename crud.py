import models
import schemas
from database import SessionLocal


def get_works_by_user_id(db: SessionLocal, user_id: int):
    return db.query(models.Work).filter(models.Work.operator_id == user_id).all()


def get_users(db: SessionLocal):
    return db.query(models.User).order_by(models.User.id).all()


def get_clients(db: SessionLocal):
    return db.query(models.Client).order_by(models.Client.id).all()


def get_sites(db: SessionLocal):
    return db.query(models.Site).order_by(models.Site.id).all()


def get_user_by_id(db: SessionLocal, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_full_name(db: SessionLocal, first_name: str, last_name: str):
    return db.query(models.User).filter(models.User.first_name == first_name,
                                            models.User.last_name == last_name).first()


def create_user(db: SessionLocal, user: schemas.UserCreate):
    db_user = models.User(first_name=user.first_name, last_name=user.last_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_table(db: SessionLocal, user_id: int, message: str):
    return db.query(models.User).filter(models.User.id == user_id, models.User.message == message).first()


def create_activity(db: SessionLocal, work: schemas.Work):
    db_work = models.Work(date=work.date, intervention_duration=work.intervention_duration,
                          intervention_type=work.intervention_type, intervention_location=work.intervention_location,
                          client=work.client, site=work.site, description=work.description, notes=work.notes,
                          trip_kms=work.trip_kms, cost=work.cost, operator_id=work.operator_id)
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work


def get_work_table(db: SessionLocal):
    result = db.query(models.Work, models.User).join(models.User, models.Work.operator_id == models.User.id).order_by(
        models.Work.id.desc()).all()
    if result:
        return result
    return 'something went wrong'
