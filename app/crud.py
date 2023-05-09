import datetime
from typing import Optional

from fastapi import HTTPException
from passlib import pwd
from sqlalchemy import literal_column, case, extract, or_

import app.auth as auth
import app.models as models
import app.schemas as schemas
from app.database import SessionLocal


def get_plant_by_client(db: SessionLocal, client_id: int):
    return db.query(models.Plant).filter(models.Plant.client_id == client_id).all()


def get_machine_by_plant(db: SessionLocal, plant_id: int):
    return db.query(models.Machine).filter(models.Machine.plant_id == plant_id).all()


def create_machine(db: SessionLocal, machine: schemas.Machine):
    db_machine = models.Machine(**machine.dict(), date_created=datetime.datetime.now())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine


def get_machines(db: SessionLocal):
    return db.query(models.Machine, models.Plant, models.Client).join(models.Plant,
                                                                      models.Machine.plant_id == models.Plant.id).join(
        models.Client, models.Plant.client_id == models.Client.id).all()


def get_reports(db: SessionLocal, user_id: Optional[int] = None):
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Machine.id.label("machine_id"),
        models.Machine.name.label("machine_name"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name")
    ).select_from(models.Report).outerjoin(models.Commission,
                                           case([(models.Report.type == "commission", models.Report.work_id)],
                                                else_=literal_column("null")).label(
                                               "commission_id") == models.Commission.id).outerjoin(models.Machine, case(
        [(models.Report.type == "machine", models.Report.work_id)], else_=literal_column("null")).label(
        "machine_id") == models.Machine.id).join(models.User, models.Report.operator_id == models.User.id).outerjoin(
        models.Plant, models.Report.type == "machine").join(models.Client,
                                                            or_(models.Plant.client_id == models.Client.id,
                                                                models.Commission.client_id == models.Client.id))

    if user_id:
        query = query.filter(models.Report.operator_id == user_id)

    return query.order_by(models.Report.date).all()


def get_report_by_id(db: SessionLocal, report_id: int):
    return db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Commission.description.label("commission_description"),
        models.Machine.id.label("machine_id"),
        models.Machine.name.label("machine_name"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name"),
    ).select_from(models.Report).outerjoin(models.Commission,
                                           case([(models.Report.type == "commission", models.Report.work_id)],
                                                else_=literal_column("null")).label(
                                               "commission_id") == models.Commission.id).outerjoin(models.Machine, case(
        [(models.Report.type == "machine", models.Report.work_id)], else_=literal_column("null")).label(
        "machine_id") == models.Machine.id).join(models.User, models.Report.operator_id == models.User.id).outerjoin(
        models.Plant, models.Report.type == "machine").join(models.Client,
                                                            or_(models.Plant.client_id == models.Client.id,
                                                                models.Commission.client_id == models.Client.id)).filter(
        models.Report.id == report_id).first()


def get_user_commissions(db: SessionLocal, user_id: int):
    return db.query(models.Commission, models.Client).join(models.Client,
                                                           models.Commission.client_id == models.Client.id).all()


def get_months(db: SessionLocal, user_id: Optional[int] = None, work_id: Optional[int] = None):
    query = db.query(models.Report.date)
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    if work_id:
        query = query.filter(models.Report.work_id == work_id)
    query = query.group_by(models.Report.date).order_by(models.Report.date)
    dates = query.all()
    return sorted(set([datetime.datetime.strftime(date[0], "%m/%Y") for date in dates]))


def get_reports_in_month(db: SessionLocal, month: str, user_id: Optional[int] = None):
    start_date = datetime.datetime.strptime(month, "%m/%Y").date()
    end_date = start_date.replace(day=28) + datetime.timedelta(days=4)
    end_date = end_date - datetime.timedelta(days=end_date.day)
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Machine.id.label("machine_id"),
        models.Machine.name.label("machine_name")
    ).select_from(models.Report) \
        .outerjoin(
        models.Commission,
        case(
            [(models.Report.type == "commission", models.Report.work_id)],
            else_=literal_column("null")
        ).label("commission_id") == models.Commission.id
    ) \
        .outerjoin(
        models.Machine,
        case(
            [(models.Report.type == "machine", models.Report.work_id)],
            else_=literal_column("null")
        ).label("machine_id") == models.Machine.id
    ) \
        .filter(
        extract('month', models.Report.date) == start_date.month,
        extract('year', models.Report.date) == start_date.year
    )
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    return query.all()


def get_reports_in_interval(db: SessionLocal, start_date: Optional[str] = None, end_date: Optional[str] = None,
                            work_id: Optional[int] = None,
                            operator_id: Optional[int] = None):
    query = db.query(models.Report, models.Commission.description.label("commission_description"),
                     models.Commission.code.label("commission_code"),
                     models.Client.name.label("client_name"), models.User.first_name, models.User.last_name).join(
        models.Commission, models.Report.work_id == models.Commission.id).join(models.Client,
                                                                               models.Commission.client_id == models.Client.id).join(
        models.User, models.Report.operator_id == models.User.id)
    if work_id != 0:
        query = query.filter(models.Report.work_id == work_id)
    if operator_id != 0:
        query = query.filter(models.Report.operator_id == operator_id)
    if start_date != '' and end_date != '':
        start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(models.Report.date >= start_date_dt,
                             models.Report.date <= end_date_dt)
    else:
        if start_date != '':
            start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(models.Report.date >= start_date_dt)
        if end_date != '':
            end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(models.Report.date <= end_date_dt)
    return query.all()


def update_report(db: SessionLocal, report_id: int, report: schemas.ReportCreate, user_id: int):
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if db_report:
        db_report.type = report.type
        db_report.date = report.date
        db_report.intervention_duration = report.intervention_duration
        db_report.intervention_type = report.intervention_type
        db_report.intervention_location = report.intervention_location
        db_report.work_id = report.work_id
        db_report.supervisor = report.supervisor
        db_report.description = report.description
        db_report.notes = report.notes
        db_report.trip_kms = report.trip_kms
        db_report.cost = report.cost
        db_report.operator_id = user_id
        db.commit()
        return db_report
    return 'C\'è stato un errore.'


def get_user_by_id(db: SessionLocal, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: SessionLocal, user: schemas.UserCreate):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username già registrato")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email già registrata")
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
        raise HTTPException(status_code=403, detail="Non puoi eliminare questo utente")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    db.delete(user)
    db.commit()
    return 'Utente eliminato'


def delete_client(db: SessionLocal, client_id: int):
    client = db.query(models.Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    db.delete(client)
    db.commit()
    return 'Cliente eliminato'


def delete_commission(db: SessionLocal, work_id: int):
    commission = db.query(models.Commission).get(work_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commessa non trovata")
    db.delete(commission)
    db.commit()
    return 'Commessa eliminata'


def delete_report(db: SessionLocal, report_id: int, user_id: int):
    report = db.query(models.Report).get(report_id)
    user = db.query(models.User).get(user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Intervento non trovato")
    if report.operator_id != user_id:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a eliminare questo intervento")
    db.delete(report)
    db.commit()
    return 'Intervento eliminato'


def create_report(db: SessionLocal, report: schemas.ReportCreate, user_id: int):
    if report.trip_kms == '':
        report.trip_kms = '0.0'
    if report.cost == '':
        report.cost = '0.0'
    db_report = models.Report(date=report.date, intervention_duration=report.intervention_duration,
                              intervention_type=report.intervention_type, type=report.type,
                              intervention_location=report.intervention_location,
                              work_id=report.work_id, description=report.description,
                              supervisor=report.supervisor,
                              notes=report.notes, trip_kms=report.trip_kms, cost=report.cost, operator_id=user_id,
                              date_created=datetime.datetime.now())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def create_commission(db: SessionLocal, commission: schemas.CommissionCreate):
    db_commission = db.query(models.Commission).filter(models.Commission.code == commission.code).first()
    if db_commission:
        raise HTTPException(status_code=400, detail="Codice commessa già registrato")
    db_commission = models.Commission(date_created=datetime.datetime.now(),
                                      code=commission.code, description=commission.description,
                                      client_id=commission.client_id)
    db.add(db_commission)
    db.commit()
    db.refresh(db_commission)
    return db_commission


def create_client(db: SessionLocal, client: schemas.Client):
    if db.query(models.Client).filter(models.Client.name == client.name).first():
        raise HTTPException(status_code=400, detail="Cliente già registrato")
    db_client = models.Client(name=client.name, address=client.address, city=client.city, email=client.email,
                              phone_number=client.phone_number, contact=client.contact,
                              date_created=datetime.datetime.now())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def get_commissions(db: SessionLocal, client_id: Optional[int] = None):
    if client_id:
        return db.query(models.Commission, models.Client).join(models.Client,
                                                               models.Commission.client_id == models.Client.id).filter(
            models.Commission.client_id == client_id).all()
    return db.query(models.Commission, models.Client).join(models.Client,
                                                           models.Commission.client_id == models.Client.id).all()
