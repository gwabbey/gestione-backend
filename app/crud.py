import datetime

from fastapi import HTTPException
from passlib import pwd
from sqlalchemy import desc

import app.auth as auth
import app.models as models
import app.schemas as schemas
from app.database import SessionLocal


def get_works_by_user_id(db: SessionLocal, user_id: int, sort_by: str = "date_created", sort_order: str = "desc"):
    valid_sort_columns = ["date_created", "last_name", "date"]
    if sort_by not in valid_sort_columns:
        sort_by = "date_created"
    if sort_order != "asc":
        sort_order = "desc"

    sort_columns = {
        "date_created": models.Work.date_created,
        "last_name": models.User.last_name,
        "date": models.Work.date
    }

    sort_column = sort_columns[sort_by]
    if sort_order == "desc":
        sort_column = desc(sort_column)

    result = db.query(models.Work, models.Site.description.label("site_description"),
                      models.Site.code.label("site_code"),
                      models.Client.name.label("client_name")).filter(models.Work.operator_id == user_id).join(
        models.Site, models.Work.site_id == models.Site.id).join(models.Client,
                                                                 models.Site.client_id == models.Client.id).order_by(
        sort_column).all()
    if result:
        return result
    return 'C\'è stato un errore.'


def get_work_table(db: SessionLocal):
    result = db.query(models.Work, models.Site.description.label("site_description"),
                      models.Site.code.label("site_code"),
                      models.Client.name.label("client_name"), models.User.first_name, models.User.last_name).join(
        models.Site, models.Work.site_id == models.Site.id).join(models.Client,
                                                                 models.Site.client_id == models.Client.id).join(
        models.User,
        models.Work.operator_id == models.User.id).all()

    if result:
        return result
    return 'C\'è stato un errore.'


def get_work_by_id(db: SessionLocal, work_id: int):
    return db.query(models.Work, models.Site.description.label("site_description"), models.Site.code.label("site_code"),
                    models.Client.name.label("client_name"), models.User.first_name, models.User.last_name).join(
        models.Site, models.Work.site_id == models.Site.id).join(models.Client,
                                                                 models.Site.client_id == models.Client.id).join(
        models.User, models.Work.operator_id == models.User.id).filter(models.Work.id == work_id).first()


def update_work(db: SessionLocal, work_id: int, work: schemas.Work, user_id: int):
    db_work = db.query(models.Work).filter(models.Work.id == work_id).first()
    if db_work:
        db_work.date = work.date
        db_work.intervention_duration = work.intervention_duration
        db_work.intervention_type = work.intervention_type
        db_work.intervention_location = work.intervention_location
        db_work.site_id = work.site_id
        db_work.description = work.description
        db_work.notes = work.notes
        db_work.trip_kms = work.trip_kms
        db_work.cost = work.cost
        db_work.operator_id = user_id
        db.commit()
        return db_work
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
    tmp_password = user.password if user.password else pwd.genword()
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


def delete_client(db: SessionLocal, client_id: int):
    client = db.query(models.Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato.")
    db.delete(client)
    db.commit()
    return 'Cliente eliminato.'


def delete_site(db: SessionLocal, site_id: int):
    site = db.query(models.Site).get(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Commessa non trovata.")
    db.delete(site)
    db.commit()
    return 'Commessa eliminata.'


def delete_work(db: SessionLocal, work_id: int, user_id: int):
    work = db.query(models.Work).get(work_id)
    user = db.query(models.User).get(user_id)
    if not work:
        raise HTTPException(status_code=404, detail="Intervento non trovato.")
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Non sei autorizzato a eliminare questo intervento.")
    if work.operator_id != user_id and user.role != 'admin':
        raise HTTPException(status_code=403, detail="Non sei autorizzato a eliminare questo intervento.")
    db.delete(work)
    db.commit()
    return 'Intervento eliminato.'


def create_work(db: SessionLocal, work: schemas.Work, user_id: int):
    if work.trip_kms == '':
        work.trip_kms = 0.0
    if work.cost == '':
        work.cost = 0.0
    db_work = models.Work(date=work.date, intervention_duration=work.intervention_duration,
                          intervention_type=work.intervention_type, intervention_location=work.intervention_location,
                          site_id=work.site_id, description=work.description,
                          notes=work.notes, trip_kms=work.trip_kms, cost=work.cost, operator_id=user_id,
                          date_created=datetime.datetime.now())
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work


def create_site(db: SessionLocal, site: schemas.SiteCreate):
    db_site = db.query(models.Site).filter(models.Site.code == site.code).first()
    if db_site:
        raise HTTPException(status_code=400, detail="Codice commessa già registrato.")
    db_site = models.Site(date_created=datetime.datetime.now(),
                          code=site.code, description=site.description, client_id=site.client_id)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


def get_sites(db: SessionLocal):
    return db.query(models.Site, models.Client).join(models.Client,
                                                     models.Site.client_id == models.Client.id).order_by(
        models.Site.id).all()


def create_client(db: SessionLocal, client: schemas.ClientCreate):
    if db.query(models.Client).filter(models.Client.name == client.name).first():
        raise HTTPException(status_code=400, detail="Cliente già registrato.")
    db_client = models.Client(name=client.name, address=client.address, city=client.city, email=client.email,
                              phone_number=client.phone_number, contact=client.contact,
                              date_created=datetime.datetime.now())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client
