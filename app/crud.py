import datetime

from fastapi import HTTPException
from passlib import pwd
from sqlalchemy import desc

import app.auth as auth
import app.models as models
import app.schemas as schemas
from app.database import SessionLocal


def get_works_by_user_id(db: SessionLocal, user_id: int, sort_by: str = "created_at", sort_order: str = "desc"):
    valid_sort_columns = ["created_at", "last_name", "date"]
    if sort_by not in valid_sort_columns:
        sort_by = "created_at"
    if sort_order != "asc":
        sort_order = "desc"

    sort_columns = {
        "created_at": models.Work.created_at,
        "last_name": models.User.last_name,
        "date": models.Work.date
    }

    sort_column = sort_columns[sort_by]
    if sort_order == "desc":
        sort_column = desc(sort_column)

    result = db.query(models.Work, models.Site.description.label("site_description"),
                      models.Client.name.label("client_name")).filter(models.Work.operator_id == user_id).join(
        models.Site, models.Work.site_id == models.Site.id).join(models.Client,
                                                                 models.Work.client_id == models.Client.id).order_by(
        sort_column).all()
    if result:
        return result
    return 'C\'è stato un errore.'


def get_work_table(db: SessionLocal, sort_by: str = "created_at", sort_order: str = "desc"):
    valid_sort_columns = ["created_at", "last_name", "date"]
    if sort_by not in valid_sort_columns:
        sort_by = "created_at"
    if sort_order != "asc":
        sort_order = "desc"

    sort_columns = {
        "created_at": models.Work.created_at,
        "last_name": models.User.last_name,
        "date": models.Work.date
    }

    sort_column = sort_columns[sort_by]
    if sort_order == "desc":
        sort_column = desc(sort_column)

    result = db.query(models.Work, models.Site.description.label("site_description"),
                      models.Client.name.label("client_name"), models.User.first_name, models.User.last_name).join(
        models.Site, models.Work.site_id == models.Site.id).join(models.Client,
                                                                 models.Work.client_id == models.Client.id).join(
        models.User,
        models.Work.operator_id == models.User.id).order_by(sort_column).all()

    if result:
        return result
    return 'C\'è stato un errore.'


def get_user_by_id(db: SessionLocal, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: SessionLocal, user: schemas.UserCreate):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username già registrato.")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email già registrata.")
    tmp_password = pwd.genword()
    tmp_password_hashed = auth.get_password_hash(tmp_password)
    if user.role == 'Operatore':
        user.role = 'user'
    if user.role == 'Dirigente':
        user.role = 'admin'
    db_user = models.User(first_name=user.first_name, last_name=user.last_name, email=user.email,
                          phone_number=user.phone_number, username=user.username, role=user.role,
                          temp_password=tmp_password, password=tmp_password_hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: SessionLocal, user_id: int, current_user_id: int):
    if user_id == 1 or user_id == current_user_id:
        raise HTTPException(status_code=403, detail="Non puoi eliminare questo utente.")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    db.delete(user)
    db.commit()
    return 'Utente eliminato.'


def delete_work(db: SessionLocal, work_id: int, user_id: int):
    work = db.query(models.Work).get(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Intervento non trovato.")
    if work.operator_id != user_id:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a eliminare questo intervento.")
    db.delete(work)
    db.commit()
    return 'Intervento eliminato.'


def create_activity(db: SessionLocal, work: schemas.Work, user_id: int):
    if work.trip_kms == '':
        work.trip_kms = 0.0
    if work.cost == '':
        work.cost = 0.0
    db_work = models.Work(date=work.date, intervention_duration=work.intervention_duration,
                          intervention_type=work.intervention_type, intervention_location=work.intervention_location,
                          client_id=work.client_id, site_id=work.site_id, description=work.description,
                          notes=work.notes, trip_kms=work.trip_kms, cost=work.cost, operator_id=user_id,
                          created_at=datetime.datetime.now())
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work


def create_site(db: SessionLocal, site: schemas.SiteCreate):
    db_site = db.query(models.Site).filter(models.Site.code == site.code).first()
    if db_site:
        raise HTTPException(status_code=400, detail="Codice commessa già registrato.")
    db_site = models.Site(date_created=datetime.datetime.now(),
                          code=site.code, description=site.description, client=site.client)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


def create_client(db: SessionLocal, client: schemas.Client):
    db_client = db.query(models.Client).filter(models.Client.name == client.name).first()
    if db_client:
        raise HTTPException(status_code=400, detail="Cliente già registrato.")
    db_client = models.Client(name=client.name, address=client.address, city=client.city, email=client.email,
                              phone_number=client.phone_number, contact=client.contact)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client
