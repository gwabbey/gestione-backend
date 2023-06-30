import datetime
from typing import Optional

from fastapi import HTTPException
from passlib import pwd
from sqlalchemy import extract, or_, and_, func, Float
from sqlalchemy.orm import aliased

import app.auth as auth
import app.models as models
import app.schemas as schemas
from app.database import SessionLocal


def get_plant_by_client(db: SessionLocal, client_id: int):
    return db.query(models.Plant).filter(models.Plant.client_id == client_id).all()


def get_machine_by_plant(db: SessionLocal, plant_id: int):
    return db.query(models.Machine).filter(models.Machine.plant_id == plant_id).order_by(models.Machine.code).all()


def create_machine(db: SessionLocal, machine: schemas.MachineCreate):
    db_machine = models.Machine(date_created=datetime.datetime.now(), name=machine.name, code=machine.code,
                                brand=machine.brand, model=machine.model, serial_number=machine.serial_number,
                                production_year=machine.production_year, cost_center=machine.cost_center,
                                description=machine.description, plant_id=machine.plant_id,
                                robotic_island=machine.robotic_island)
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine


def get_plants(db: SessionLocal):
    return db.query(models.Plant, models.Client).join(models.Client,
                                                      models.Plant.client_id == models.Client.id).order_by(
        models.Plant.id).all()


def get_machines(db: SessionLocal, limit: Optional[int] = None):
    return db.query(models.Machine, models.Plant, models.Client).join(models.Plant,
                                                                      models.Machine.plant_id == models.Plant.id).join(
        models.Client, models.Plant.client_id == models.Client.id).order_by(models.Machine.code).limit(limit).all()


def get_reports(db: SessionLocal, user_id: Optional[int] = None, limit: Optional[int] = None):
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Machine.id.label("machine_id"),
        models.Machine.name.label("machine_name"),
        models.Machine.cost_center.label("cost_center"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name"),
        models.Plant.id.label("plant_id"),
        models.Plant.city.label("plant_city"),
        models.Plant.address.label("plant_address")
    ).select_from(models.Report).outerjoin(models.Commission,
                                           and_(models.Report.type == "commission",
                                                models.Report.work_id == models.Commission.id)).outerjoin(
        models.Machine, and_(models.Report.type == "machine",
                             models.Report.work_id == models.Machine.id)).join(models.User,
                                                                               models.Report.operator_id == models.
                                                                               User.id).outerjoin(
        models.Plant, and_(models.Report.type == "machine", models.Machine.plant_id == models.Plant.id)).join(
        models.Client,
        or_(models.Commission.client_id == models.Client.id,
            and_(models.Plant.client_id == models.Client.id,
                 models.Report.type == "machine")))
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    return query.order_by(models.Report.date.desc()).limit(limit).all()


def get_report_by_id(db: SessionLocal, report_id: int):
    supervisor = aliased(models.User)
    return db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Commission.description.label("commission_description"),
        models.Machine.id.label("machine_id"),
        models.Machine.code.label("machine_code"),
        models.Machine.cost_center.label("cost_center"),
        models.Machine.name.label("machine_name"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name"),
        models.Client.city.label("client_city"),
        models.Plant.id.label("plant_id"),
        models.Plant.name.label("plant_name"),
        models.Plant.city.label("plant_city"),
        models.Plant.address.label("plant_address"),
        supervisor.id.label("supervisor_id"),
        supervisor.first_name.label("supervisor_first_name"),
        supervisor.last_name.label("supervisor_last_name")
    ).select_from(models.Report).outerjoin(
        models.Commission,
        and_(models.Report.type == "commission", models.Report.work_id == models.Commission.id)).outerjoin(
        models.Machine, and_(models.Report.type == "machine", models.Report.work_id == models.Machine.id)).join(
        models.User, models.Report.operator_id == models.User.id).outerjoin(
        models.Plant, models.Machine.plant_id == models.Plant.id
    ).join(
        models.Client,
        or_(models.Plant.client_id == models.Client.id, models.Commission.client_id == models.Client.id)
    ).join(supervisor, models.Report.supervisor_id == supervisor.id
           ).filter(models.Report.id == report_id).first()


def get_months(db: SessionLocal, user_id: Optional[int] = None, client_id: Optional[int] = None):
    query = db.query(models.Report.date)
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    if client_id:
        query = query.filter(models.Client.id == client_id)
    query = query.group_by(models.Report.date).order_by(models.Report.date)
    dates = query.all()
    return sorted(set([datetime.datetime.strftime(date[0], "%m/%Y") for date in dates]))


def get_monthly_reports(db: SessionLocal, month: Optional[str] = '0', user_id: Optional[int] = 0,
                        client_id: Optional[int] = 0,
                        plant_id: Optional[int] = 0, work_id: Optional[int] = 0):
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Commission.description.label("commission_description"),
        models.Machine.id.label("machine_id"),
        models.Machine.name.label("machine_name"),
        models.Machine.cost_center.label("cost_center"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name"),
        models.Plant.id.label("plant_id"),
        models.Plant.name.label("plant_name"),
        models.Plant.city.label("plant_city"),
        models.Plant.address.label("plant_address")
    ).select_from(models.Report).outerjoin(
        models.Commission,
        and_(models.Report.type == "commission", models.Report.work_id == models.Commission.id)
    ).outerjoin(
        models.Machine,
        and_(models.Report.type == "machine", models.Report.work_id == models.Machine.id)
    ).join(models.User, models.Report.operator_id == models.User.id).outerjoin(
        models.Plant, models.Machine.plant_id == models.Plant.id
    ).join(
        models.Client,
        or_(models.Plant.client_id == models.Client.id, models.Commission.client_id == models.Client.id)
    )
    if month != '0':
        start_date = datetime.datetime.strptime(month, "%m/%Y").date()
        query = query.filter(
            extract('month', models.Report.date) == start_date.month,
            extract('year', models.Report.date) == start_date.year
        )
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    if client_id:
        query = query.filter(models.Client.id == client_id)
    if plant_id == 0:
        query = query.filter(models.Report.type == "machine")
    if plant_id != 0:
        query = query.filter(models.Plant.id == plant_id)
    if work_id:
        query = query.filter(models.Report.work_id == work_id)
    return query.order_by(models.Report.date).all()


def get_interval_reports(db: SessionLocal, start_date: Optional[str] = None, end_date: Optional[str] = None,
                         user_id: Optional[int] = 0,
                         client_id: Optional[int] = 0,
                         plant_id: Optional[int] = 0, work_id: Optional[int] = 0):
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Commission.description.label("commission_description"),
        models.Machine.id.label("machine_id"),
        models.Machine.name.label("machine_name"),
        models.Machine.cost_center.label("cost_center"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name"),
        models.Plant.id.label("plant_id"),
        models.Plant.name.label("plant_name"),
        models.Plant.city.label("plant_city"),
        models.Plant.address.label("plant_address")
    ).select_from(models.Report).outerjoin(
        models.Commission,
        and_(models.Report.type == "commission", models.Report.work_id == models.Commission.id)
    ).outerjoin(
        models.Machine,
        and_(models.Report.type == "machine", models.Report.work_id == models.Machine.id)
    ).join(models.User, models.Report.operator_id == models.User.id).outerjoin(
        models.Plant, models.Machine.plant_id == models.Plant.id
    ).join(
        models.Client,
        or_(models.Plant.client_id == models.Client.id, models.Commission.client_id == models.Client.id)
    )
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
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    if client_id:
        query = query.filter(models.Client.id == client_id)
    if plant_id == 0:
        query = query.filter(models.Report.type == "machine")
    if plant_id != 0:
        query = query.filter(models.Plant.id == plant_id)
    if work_id:
        query = query.filter(models.Report.work_id == work_id)
    return query.order_by(models.Report.date).all()


def get_monthly_commission_reports(db: SessionLocal, month: str, user_id: Optional[int] = None,
                                   client_id: Optional[int] = None, work_id: Optional[int] = None):
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Commission.description.label("commission_description"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name")
    ).select_from(models.Report).join(
        models.Commission,
        and_(models.Report.type == "commission", models.Report.work_id == models.Commission.id)
    ).join(models.User, models.Report.operator_id == models.User.id).join(
        models.Client, models.Commission.client_id == models.Client.id
    )
    if month != '0':
        start_date = datetime.datetime.strptime(month, "%m/%Y").date()
        query = query.filter(
            extract('month', models.Report.date) == start_date.month,
            extract('year', models.Report.date) == start_date.year
        )
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    if client_id:
        query = query.filter(models.Client.id == client_id)
    if work_id:
        query = query.filter(models.Report.work_id == work_id)
    return query.order_by(models.Report.date).all()


def get_interval_commission_reports(db: SessionLocal, start_date: Optional[str] = None, end_date: Optional[str] = None,
                                    user_id: Optional[int] = None,
                                    client_id: Optional[int] = None, work_id: Optional[int] = None):
    query = db.query(
        models.Report,
        models.Commission.id.label("commission_id"),
        models.Commission.code.label("commission_code"),
        models.Commission.description.label("commission_description"),
        models.User.id.label("operator_id"),
        models.User.first_name,
        models.User.last_name,
        models.Client.id.label("client_id"),
        models.Client.name.label("client_name")
    ).select_from(models.Report).join(
        models.Commission,
        and_(models.Report.type == "commission", models.Report.work_id == models.Commission.id)
    ).join(models.User, models.Report.operator_id == models.User.id).join(
        models.Client, models.Commission.client_id == models.Client.id
    )
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
    if user_id:
        query = query.filter(models.Report.operator_id == user_id)
    if client_id:
        query = query.filter(models.Client.id == client_id)
    if work_id:
        query = query.filter(models.Report.work_id == work_id)
    return query.order_by(models.Report.date).all()


def get_daily_hours_in_month(db: SessionLocal, month: str, user_id: int):
    start_date = datetime.datetime.strptime(month, "%m/%Y").date()
    end_date = (start_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += datetime.timedelta(days=1)
    query = db.query(
        func.date_trunc('day', models.Report.date).label('day'),
        func.sum(func.cast(models.Report.intervention_duration, Float)).label('hours'),
        func.count().label('count')
    ).filter(
        models.Report.date >= start_date,
        models.Report.date < end_date + datetime.timedelta(days=1),
        models.Report.operator_id == user_id
    ).group_by(
        func.date_trunc('day', models.Report.date)
    ).order_by(
        func.date_trunc('day', models.Report.date)
    )
    items = query.all()
    result = []
    for date in dates:
        result_dict = {'date': date.strftime('%d/%m/%Y'), 'hours': 0, 'count': 0}
        for item in items:
            if item.day.date() == date:
                result_dict['hours'] = item.hours
                result_dict['count'] = item.count
                break
        result.append(result_dict)
    return result


def edit_report(db: SessionLocal, report_id: int, report: schemas.ReportCreate, user_id: int):
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if db_report:
        db_report.type = report.type
        db_report.date = report.date
        db_report.intervention_duration = report.intervention_duration
        db_report.intervention_type = report.intervention_type
        db_report.intervention_location = report.intervention_location
        db_report.work_id = report.work_id
        db_report.supervisor_id = report.supervisor_id
        db_report.description = report.description
        db_report.notes = report.notes
        db_report.trip_kms = report.trip_kms
        db_report.cost = report.cost
        db_report.operator_id = user_id
        db.commit()
        return db_report
    return {"detail": "Errore"}, 400


def edit_client(db: SessionLocal, client_id: int, client: schemas.ClientCreate):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client:
        db_client.name = client.name
        db_client.city = client.city
        db_client.address = client.address
        db_client.email = client.email
        db_client.contact = client.contact
        db_client.phone_number = client.phone_number
        db_client.province = client.province
        db_client.cap = client.cap
        db.commit()
        return db_client
    return {"detail": "Errore"}, 400


def edit_commission(db: SessionLocal, commission_id: int, commission: schemas.CommissionCreate):
    db_commission = db.query(models.Commission).filter(models.Commission.id == commission_id).first()
    if db_commission:
        db_commission.client_id = commission.client_id
        db_commission.code = commission.code
        db_commission.description = commission.description
        db_commission.status = commission.status
        db.commit()
        return db_commission
    return {"detail": "Errore"}, 400


def edit_plant(db: SessionLocal, plant_id: int, plant: schemas.PlantCreate):
    db_plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if db_plant:
        db_plant.client_id = plant.client_id
        db_plant.name = plant.name
        db_plant.city = plant.city
        db_plant.address = plant.address
        db_plant.email = plant.email
        db_plant.contact = plant.contact
        db_plant.phone_number = plant.phone_number
        db_plant.province = plant.province
        db_plant.cap = plant.cap
        db.commit()
        return db_plant
    return {"detail": "Errore"}, 400


def edit_machine(db: SessionLocal, machine_id: int, machine: schemas.MachineCreate):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if db_machine:
        db_machine.plant_id = machine.plant_id
        db_machine.robotic_island = machine.robotic_island
        db_machine.code = machine.code
        db_machine.name = machine.name
        db_machine.brand = machine.brand
        db_machine.model = machine.model
        db_machine.serial_number = machine.serial_number
        db_machine.production_year = machine.production_year
        db_machine.cost_center = machine.cost_center
        db_machine.description = machine.description
        db.commit()
        return db_machine
    return {"detail": "Errore"}, 400


def get_user_by_id(db: SessionLocal, user_id: int):
    return db.query(models.User, models.Role.name.label('role'), models.Client.name.label('client_name'),
                    models.Client.city.label('client_city')).join(models.Role,
                                                                  models.User.role_id == models.Role.id).join(
        models.Client, models.User.client_id == models.Client.id).filter(models.User.id == user_id).first()


def get_client_by_id(db: SessionLocal, client_id: int):
    return db.query(models.Client).filter(models.Client.id == client_id).first()


def get_plant_by_id(db: SessionLocal, plant_id: int):
    return db.query(models.Plant, models.Client).filter(models.Plant.id == plant_id).join(
        models.Client,
        models.Plant.client_id == models.Client.id).first()


def get_commission_by_id(db: SessionLocal, commission_id: int):
    return db.query(models.Commission, models.Client).filter(models.Commission.id == commission_id).join(
        models.Client,
        models.Commission.client_id == models.Client.id).first()


def get_machine_by_id(db: SessionLocal, machine_id: int):
    return db.query(models.Machine, models.Plant, models.Client).filter(models.Machine.id == machine_id).join(
        models.Plant,
        models.Machine.plant_id == models.Plant.id).join(
        models.Client, models.Plant.client_id == models.Client.id).first()


def create_user(db: SessionLocal, user: schemas.UserCreate):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username già registrato")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email già registrata")
    tmp_password = user.password if user.password else pwd.genword()
    tmp_password_hashed = auth.get_password_hash(tmp_password)
    db_user = models.User(first_name=user.first_name, last_name=user.last_name, email=user.email,
                          phone_number=user.phone_number, username=user.username, role_id=user.role_id,
                          client_id=user.client_id, temp_password=tmp_password, password=tmp_password_hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: SessionLocal, user_id: int, current_user_id: int):
    user = db.query(models.User).get(user_id)
    if user_id == 1 or user_id == current_user_id or db.query(models.User).filter(
            models.Report.operator_id == user_id).first() or db.query(models.User).filter(
        models.Report.supervisor_id == user_id).first():
        raise HTTPException(status_code=403, detail="Non puoi eliminare questo utente")
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    db.delete(user)
    db.commit()
    return {"detail": "Utente eliminato"}


def delete_client(db: SessionLocal, client_id: int):
    client = db.query(models.Client).get(client_id)
    exists = db.query(models.Commission).filter(models.Commission.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    if exists:
        raise HTTPException(status_code=400, detail="Non puoi eliminare questo cliente")
    db.delete(client)
    db.commit()
    return {"detail": "Cliente eliminato"}


def delete_commission(db: SessionLocal, commission_id: int):
    commission = db.query(models.Commission).get(commission_id)
    exists = db.query(models.Report).filter(models.Report.work_id == commission_id).filter(
        models.Report.type == 'commission').first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commessa non trovata")
    if exists:
        raise HTTPException(status_code=400, detail="Non puoi eliminare questa commessa")
    db.delete(commission)
    db.commit()
    return {"detail": "Commessa eliminata"}


def delete_machine(db: SessionLocal, machine_id: int):
    machine = db.query(models.Machine).get(machine_id)
    exists = db.query(models.Report).filter(models.Report.work_id == machine_id).filter(
        models.Report.type == 'machine').first()
    if not machine:
        raise HTTPException(status_code=404, detail="Macchina non trovata")
    if exists:
        raise HTTPException(status_code=400, detail="Non puoi eliminare questa macchina")
    db.delete(machine)
    db.commit()
    return {"detail": "Macchina eliminata"}


def delete_plant(db: SessionLocal, plant_id: int):
    plant = db.query(models.Plant).get(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Stabilimento non trovato")
    exists = db.query(models.Machine).filter(models.Machine.plant_id == plant_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="Non puoi eliminare questo stabilimento")
    db.delete(plant)
    db.commit()
    return {"detail": "Stabilimento eliminato"}


def delete_report(db: SessionLocal, report_id: int, user_id: int):
    report = db.query(models.Report).get(report_id)
    user = db.query(models.User).get(user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Intervento non trovato")
    if report.operator_id != user_id and user.role_id != 1:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a eliminare questo intervento")
    db.delete(report)
    db.commit()
    return {"detail": "Intervento eliminato"}


def create_report(db: SessionLocal, report: schemas.ReportCreate, user_id: int):
    if report.trip_kms == '':
        report.trip_kms = '0.0'
    if report.cost == '':
        report.cost = '0.0'
    db_report = models.Report(date=report.date, intervention_duration=report.intervention_duration,
                              intervention_type=report.intervention_type, type=report.type,
                              intervention_location=report.intervention_location,
                              work_id=report.work_id, description=report.description,
                              supervisor_id=report.supervisor_id,
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
                                      client_id=commission.client_id, status='on')
    db.add(db_commission)
    db.commit()
    db.refresh(db_commission)
    return db_commission


def create_client(db: SessionLocal, client: schemas.ClientCreate):
    if db.query(models.Client).filter(models.Client.name == client.name).first():
        raise HTTPException(status_code=400, detail="Cliente già registrato")
    db_client = models.Client(name=client.name, address=client.address, city=client.city, email=client.email,
                              phone_number=client.phone_number, contact=client.contact, province=client.province,
                              cap=client.cap,
                              date_created=datetime.datetime.now())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def get_commissions(db: SessionLocal, client_id: Optional[int] = None):
    query = db.query(models.Commission, models.Client).join(models.Client,
                                                            models.Commission.client_id == models.Client.id)
    if client_id:
        query = query.filter(
            models.Commission.client_id == client_id)
    return query.order_by(models.Client.name).all()


def create_plant(db: SessionLocal, plant: schemas.PlantCreate):
    exists = db.query(models.Plant).filter(models.Plant.address == plant.address).first()
    if exists:
        raise HTTPException(status_code=400, detail="Esiste già uno stabilimento con questo indirizzo")
    db_plant = models.Plant(date_created=datetime.datetime.now(), name=plant.name, address=plant.address,
                            province=plant.province, cap=plant.cap,
                            city=plant.city, email=plant.email, phone_number=plant.phone_number, contact=plant.contact,
                            client_id=plant.client_id)
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant


def change_password(db: SessionLocal, old_password: str, new_password: str, user_id: int):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="La password deve essere lunga almeno 8 caratteri")
    if ' ' in new_password:
        raise HTTPException(status_code=400, detail="La password non può contenere spazi")
    if old_password == new_password:
        raise HTTPException(status_code=400, detail="La password nuova deve essere diversa da quella attuale")
    if not auth.verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="Password errata")
    user.password = auth.get_password_hash(new_password)
    db.commit()
    return {"detail": "Password modificata"}


def edit_user(db: SessionLocal, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.email = user.email
        db_user.phone_number = user.phone_number
        if db_user.client_id != user.client_id:
            db_user.client_id = user.client_id
        db.commit()
        return db_user
    return {"detail": "Errore"}, 400


def get_supervisors_by_client(db: SessionLocal, client_id: int):
    return db.query(models.User).filter(models.User.client_id == client_id).all()


def reset_password(db: SessionLocal, user_id: int):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    tmp_password = pwd.genword()
    tmp_password_hashed = auth.get_password_hash(tmp_password)
    user.temp_password = tmp_password
    user.password = tmp_password_hashed
    db.commit()
    db.refresh(user)
    return {"detail": "Password resettata", "password": tmp_password}


def edit_report_email_date(db: SessionLocal, report_id: int, email_date: datetime.datetime):
    db_report = db.query(models.Report).get(report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Intervento non trovato")
    db_report.email_date = email_date
    db.commit()
    db.refresh(db_report)
    return db_report
