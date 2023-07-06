import csv
import datetime
import os
from datetime import timedelta
from io import BytesIO
from typing import Optional
from zoneinfo import ZoneInfo

import xmltodict
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, Form, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_mail import ConnectionConfig, FastMail, MessageType, MessageSchema
from jinja2 import Template
from pydantic import BaseSettings, EmailStr
from pypdf import PdfWriter
from sqlalchemy import or_
from starlette.background import BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response, FileResponse
from weasyprint import HTML

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token, get_current_user, is_admin
from app.database import SessionLocal, engine, get_db

load_dotenv()
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS"))

models.Base.metadata.create_all(bind=engine)


class Settings(BaseSettings):
    openapi_url: str = os.getenv("OPENAPI_URL")


settings = Settings()

app = FastAPI(openapi_url=settings.openapi_url, docs_url=None, redoc_url=None)

openapi_url = settings.openapi_url

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM="manutenzione@moveautomation.it",
    MAIL_PORT=587,
    MAIL_FROM_NAME="Move Automation S.r.l.",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username o password errati.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users", response_model=list[schemas.User])
def get_all_users(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(is_admin)):
    return db.query(models.User).order_by(models.User.last_name).all()


@app.get("/operators", response_model=list[schemas.User])
def get_operators(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(is_admin)):
    return db.query(models.User).join(models.Role).order_by(models.User.last_name).filter(
        or_(models.Role.id == 1, models.Role.id == 2)).all()


@app.get("/clients", response_model=list[schemas.Client])
def get_clients(db: SessionLocal = Depends(get_db)):
    return db.query(models.Client).order_by(models.Client.id).all()


@app.get("/commissions")
def get_commissions(db: SessionLocal = Depends(get_db), client_id: Optional[int] = None,
                    current_user: schemas.User = Depends(is_admin)):
    if client_id:
        return crud.get_commissions(db, client_id=client_id)
    return crud.get_commissions(db)


@app.get("/commissions/open")
def get_open_commissions(db: SessionLocal = Depends(get_db), client_id: Optional[int] = None,
                         current_user: models.User = Depends(get_current_user)):
    if client_id:
        return crud.get_open_commissions(db, client_id=client_id)
    return crud.get_open_commissions(db)


@app.get("/roles", response_model=list[schemas.Role])
def get_roles(db: SessionLocal = Depends(get_db)):
    return db.query(models.Role).order_by(models.Role.id).all()


@app.get("/intervention_types", response_model=list[schemas.InterventionType])
def get_intervention_types(db: SessionLocal = Depends(get_db)):
    return db.query(models.InterventionType).order_by(models.InterventionType.id).all()


@app.get("/locations", response_model=list[schemas.Location])
def get_locations(db: SessionLocal = Depends(get_db)):
    return db.query(models.Location).order_by(models.Location.id).all()


@app.get("/plants")
def get_plants(db: SessionLocal = Depends(get_db)):
    return crud.get_plants(db)


@app.get("/machines")
def get_machines(db: SessionLocal = Depends(get_db), limit: Optional[int] = None):
    return crud.get_machines(db, limit=limit)


@app.get("/reports")
def get_reports(current_user: models.User = Depends(is_admin),
                db: SessionLocal = Depends(get_db), limit: Optional[int] = None):
    return crud.get_reports(db, limit=limit)


@app.get("/plant")
def get_plant_by_client(db: SessionLocal = Depends(get_db), client_id: int = None):
    return crud.get_plant_by_client(db, client_id=client_id)


@app.get("/machine")
def get_machine_by_plant(db: SessionLocal = Depends(get_db), plant_id: int = None):
    return crud.get_machine_by_plant(db, plant_id=plant_id)


@app.get("/supervisors")
def get_supervisors_by_client(db: SessionLocal = Depends(get_db), client_id: int = None):
    return crud.get_supervisors_by_client(db, client_id=client_id)


@app.get("/months")
def get_months(db: SessionLocal = Depends(get_db), user_id: Optional[int] = None, client_id: Optional[int] = None):
    if user_id:
        return crud.get_months(db, user_id=user_id)
    elif client_id:
        return crud.get_months(db, client_id=client_id)
    return crud.get_months(db)


@app.get("/me/months")
def get_my_months(db: SessionLocal = Depends(get_db), current_user: models.User = Depends(get_current_user),
                  client_id: Optional[int] = None):
    if client_id:
        return crud.get_months(db, user_id=current_user.id, client_id=client_id)
    return crud.get_months(db, user_id=current_user.id)


@app.get("/reports/monthly")
def get_monthly_reports(month: Optional[str] = None, db: SessionLocal = Depends(get_db),
                        user_id: Optional[int] = None, client_id: Optional[int] = None, plant_id: Optional[int] = None,
                        work_id: Optional[int] = None):
    return crud.get_monthly_reports(month=month, user_id=user_id, client_id=client_id, plant_id=plant_id,
                                    work_id=work_id, db=db)


@app.get("/reports/monthly/commissions")
def get_monthly_commission_reports(month: str, db: SessionLocal = Depends(get_db),
                                   user_id: Optional[int] = None, client_id: Optional[int] = None,
                                   work_id: Optional[int] = None):
    return crud.get_monthly_commission_reports(month=month, user_id=user_id, client_id=client_id, db=db,
                                               work_id=work_id)


@app.get("/reports/interval")
def get_interval_reports(start_date: Optional[str] = None, end_date: Optional[str] = None,
                         db: SessionLocal = Depends(get_db), user_id: Optional[int] = None,
                         client_id: Optional[int] = None, plant_id: Optional[int] = None,
                         work_id: Optional[int] = None):
    return crud.get_interval_reports(start_date=start_date, end_date=end_date, user_id=user_id, client_id=client_id,
                                     plant_id=plant_id, work_id=work_id, db=db)


@app.get("/reports/interval/commissions")
def get_interval_commission_reports(start_date: Optional[str] = None, end_date: Optional[str] = None,
                                    db: SessionLocal = Depends(get_db), user_id: Optional[int] = None,
                                    client_id: Optional[int] = None, work_id: Optional[int] = None):
    return crud.get_interval_commission_reports(start_date=start_date, end_date=end_date, user_id=user_id,
                                                client_id=client_id, work_id=work_id, db=db)


@app.get("/reports/daily")
def get_daily_hours_in_month(month: str, user_id: Optional[int] = None, db: SessionLocal = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Non sei autorizzato ad accedere a questa risorsa")
    return crud.get_daily_hours_in_month(month=month, db=db, user_id=user_id)


@app.get("/report/{report_id}")
def get_report_by_id(report_id: int, db: SessionLocal = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    report = crud.get_report_by_id(db, report_id=report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Intervento non trovato")
    if db.query(models.Report).filter(
            models.Report.id == report_id).first().operator_id != current_user.id and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a vedere questo intervento")
    return report


@app.get("/report/{report_id}/pdf")
def get_pdf_report(report_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    if not current_user.id:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a vedere questo intervento")
    report = crud.get_report_by_id(db, report_id=report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Intervento non trovato")
    with open('app/result.html') as file:
        template = Template(file.read())
    rendered_html = template.render(report=report)
    pdf = HTML(string=rendered_html).write_pdf(presentational_hints=True)
    return Response(content=pdf, media_type="application/pdf")


@app.get("/reports/monthly/csv")
def get_csv_monthly_reports(month: str, db: SessionLocal = Depends(get_db),
                            user_id: Optional[int] = None, client_id: Optional[int] = None,
                            plant_id: Optional[int] = None, work_id: Optional[int] = None):
    reports = crud.get_monthly_reports(month=month, user_id=user_id, client_id=client_id, plant_id=plant_id,
                                       work_id=work_id, db=db)
    with open('app/test.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(
            ['Operatore', 'Data', 'Cliente', 'Stabilimento', 'Durata', 'Tipo', 'Macchina', 'Centro di costo',
             'Location', 'Descrizione'])
        filename = 'interventi_' + month + '.csv'
        for report in reports:
            csvwriter.writerow([report.first_name + ' ' + report.last_name, report.Report.date.strftime("%d/%m/%Y"),
                                report.client_name,
                                report.plant_city + ' ' + report.plant_address,
                                report.Report.intervention_duration.replace('.', ','),
                                report.Report.intervention_type, report.machine_name,
                                report.cost_center, report.Report.intervention_location,
                                report.Report.description])
        total_hours = [report.Report.intervention_duration for report in reports]
        total_hours = sum([float(i.replace(',', '.')) for i in total_hours])
        csvwriter.writerow('')
        csvwriter.writerow(['Totale ore', '', '', '', str(total_hours).replace('.', ','), '', '', '', '', ''])
    return FileResponse('app/test.csv', filename=filename)


@app.get("/reports/interval/csv")
def get_csv_interval_reports(start_date: str, end_date: str, db: SessionLocal = Depends(get_db),
                             user_id: Optional[int] = None, client_id: Optional[int] = None,
                             plant_id: Optional[int] = None, work_id: Optional[int] = None):
    reports = crud.get_interval_reports(start_date=start_date, end_date=end_date, user_id=user_id, client_id=client_id,
                                        plant_id=plant_id, work_id=work_id, db=db)
    with open('app/test.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(
            ['Operatore', 'Data', 'Cliente', 'Stabilimento', 'Durata', 'Tipo', 'Macchina', 'Centro di costo',
             'Location', 'Descrizione'])
        filename = 'interventi_' + '.csv'
        for report in reports:
            csvwriter.writerow([report.first_name + ' ' + report.last_name, report.Report.date.strftime("%d/%m/%Y"),
                                report.client_name,
                                report.plant_city + ' ' + report.plant_address,
                                report.Report.intervention_duration.replace('.', ','),
                                report.Report.intervention_type, report.machine_name,
                                report.cost_center, report.Report.intervention_location,
                                report.Report.description])
        total_hours = [report.Report.intervention_duration for report in reports]
        total_hours = sum([float(i.replace(',', '.')) for i in total_hours])
        csvwriter.writerow('')
        csvwriter.writerow(['Totale ore', '', '', '', str(total_hours).replace('.', ','), '', '', '', '', ''])
    return FileResponse('app/test.csv', filename=filename)


@app.get("/reports/monthly/pdf")
def get_pdf_monthly_reports(month: str, db: SessionLocal = Depends(get_db),
                            user_id: Optional[int] = None, client_id: Optional[int] = None,
                            plant_id: Optional[int] = None, work_id: Optional[int] = None):
    merger = PdfWriter()
    reports = crud.get_monthly_reports(month=month, user_id=user_id, client_id=client_id, plant_id=plant_id,
                                       work_id=work_id, db=db)
    for report in reports:
        with open('app/result.html') as file:
            template = Template(file.read())
        rendered_html = template.render(report=report)
        pdf = HTML(string=rendered_html).write_pdf(presentational_hints=True)
        merger.append(BytesIO(pdf))
    output = BytesIO()
    merger.write(output)
    output.seek(0)
    return Response(content=output.getvalue(), media_type="application/pdf")


@app.get("/reports/monthly/commissions/pdf")
def get_pdf_monthly_commission_reports(month: str, db: SessionLocal = Depends(get_db),
                                       user_id: Optional[int] = None, client_id: Optional[int] = None,
                                       work_id: Optional[int] = None):
    merger = PdfWriter()
    reports = crud.get_monthly_commission_reports(month=month, user_id=user_id, client_id=client_id, work_id=work_id,
                                                  db=db)
    for report in reports:
        with open('app/result.html') as file:
            template = Template(file.read())
        rendered_html = template.render(report=report)
        pdf = HTML(string=rendered_html).write_pdf(presentational_hints=True)
        merger.append(BytesIO(pdf))
    output = BytesIO()
    merger.write(output)
    output.seek(0)
    return Response(content=output.getvalue(), media_type="application/pdf")


@app.get("/reports/interval/pdf")
def get_pdf_interval_reports(start_date: Optional[str] = None, end_date: Optional[str] = None,
                             db: SessionLocal = Depends(get_db), user_id: Optional[int] = None,
                             client_id: Optional[int] = None, plant_id: Optional[int] = None,
                             work_id: Optional[int] = None):
    merger = PdfWriter()
    reports = crud.get_interval_reports(start_date=start_date, end_date=end_date, user_id=user_id, client_id=client_id,
                                        plant_id=plant_id, work_id=work_id, db=db)
    for report in reports:
        with open('app/result.html') as file:
            template = Template(file.read())
        rendered_html = template.render(report=report)
        pdf = HTML(string=rendered_html).write_pdf(presentational_hints=True)
        merger.append(BytesIO(pdf))
    output = BytesIO()
    merger.write(output)
    output.seek(0)
    return Response(content=output.getvalue(), media_type="application/pdf")


@app.get("/reports/interval/commissions/pdf")
def get_pdf_interval_commission_reports(start_date: Optional[str] = None, end_date: Optional[str] = None,
                                        db: SessionLocal = Depends(get_db),
                                        user_id: Optional[int] = None, client_id: Optional[int] = None,
                                        work_id: Optional[int] = None):
    merger = PdfWriter()
    reports = crud.get_interval_commission_reports(start_date=start_date, end_date=end_date, user_id=user_id,
                                                   client_id=client_id, work_id=work_id, db=db)
    for report in reports:
        with open('app/result.html') as file:
            template = Template(file.read())
        rendered_html = template.render(report=report)
        pdf = HTML(string=rendered_html).write_pdf(presentational_hints=True)
        merger.append(BytesIO(pdf))
    output = BytesIO()
    merger.write(output)
    output.seek(0)
    return Response(content=output.getvalue(), media_type="application/pdf")


@app.get("/reports/monthly/commissions/csv")
def get_csv_monthly_commission_reports(month: str, db: SessionLocal = Depends(get_db),
                                       user_id: Optional[int] = None, client_id: Optional[int] = None,
                                       work_id: Optional[int] = None):
    reports = crud.get_monthly_commission_reports(month=month, user_id=user_id, client_id=client_id, work_id=work_id,
                                                  db=db)
    with open('app/test.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(
            ['Operatore', 'Data', 'Cliente', 'Commessa', 'Durata', 'Tipo', 'Location', 'Descrizione'])
        filename = 'interventi_' + month + '.csv'
        for report in reports:
            csvwriter.writerow([report.first_name + ' ' + report.last_name, report.Report.date.strftime("%d/%m/%Y"),
                                report.client_name,
                                report.commission_code + ' - ' + report.commission_description,
                                report.Report.intervention_duration.replace('.', ','),
                                report.Report.intervention_type, report.Report.intervention_location,
                                report.Report.description])
        total_hours = [report.Report.intervention_duration for report in reports]
        total_hours = sum([float(i.replace(',', '.')) for i in total_hours])
        csvwriter.writerow('')
        csvwriter.writerow(['Totale ore', '', '', '', str(total_hours).replace('.', ','), '', '', ''])
    return FileResponse('app/test.csv', filename=filename)


@app.get("/reports/interval/commissions/csv")
def get_csv_interval_commission_reports(start_date: str, end_date: str, db: SessionLocal = Depends(get_db),
                                        user_id: Optional[int] = None, client_id: Optional[int] = None,
                                        work_id: Optional[int] = None):
    reports = crud.get_interval_commission_reports(start_date=start_date, end_date=end_date, user_id=user_id,
                                                   client_id=client_id, work_id=work_id,
                                                   db=db)
    with open('app/test.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(
            ['Operatore', 'Data', 'Cliente', 'Commessa', 'Durata', 'Tipo', 'Location', 'Descrizione'])
        filename = 'interventi.csv'
        for report in reports:
            csvwriter.writerow([report.first_name + ' ' + report.last_name, report.Report.date.strftime("%d/%m/%Y"),
                                report.client_name,
                                report.commission_code + ' - ' + report.commission_description,
                                report.Report.intervention_duration.replace('.', ','),
                                report.Report.intervention_type, report.Report.intervention_location,
                                report.Report.description])
        total_hours = [report.Report.intervention_duration for report in reports]
        total_hours = sum([float(i.replace(',', '.')) for i in total_hours])
        csvwriter.writerow('')
        csvwriter.writerow(['Totale ore', '', '', '', str(total_hours).replace('.', ','), '', '', ''])
    return FileResponse('app/test.csv', filename=filename)


@app.get("/me")
async def get_profile(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_user_by_id(db, user_id=current_user.id)


@app.get("/me/reports")
def get_my_reports(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user),
                   limit: Optional[int] = None):
    return crud.get_reports(db=db, user_id=current_user.id, limit=limit)


@app.get("/user/{user_id}")
def get_user_by_id(user_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(is_admin)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return db_user


@app.get("/client/{client_id}", response_model=schemas.Client)
def get_client_by_id(client_id: int, db: SessionLocal = Depends(get_db),
                     current_user: models.User = Depends(is_admin)):
    db_client = crud.get_client_by_id(db, client_id=client_id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return db_client


@app.get("/plant/{plant_id}")
def get_plant_by_id(plant_id: int, db: SessionLocal = Depends(get_db),
                    current_user: models.User = Depends(is_admin)):
    db_plant = crud.get_plant_by_id(db, plant_id=plant_id)
    if db_plant is None:
        raise HTTPException(status_code=404, detail="Stabilimento non trovato")
    return db_plant


@app.get("/commission/{commission_id}")
def get_commission_by_id(commission_id: int, db: SessionLocal = Depends(get_db),
                         current_user: models.User = Depends(is_admin)):
    db_commission = crud.get_commission_by_id(db, commission_id=commission_id)
    if db_commission is None:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return db_commission


@app.get("/machine/{machine_id}")
def get_machine_by_id(machine_id: int, db: SessionLocal = Depends(get_db),
                      current_user: models.User = Depends(is_admin)):
    db_machine = crud.get_machine_by_id(db, machine_id=machine_id)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Macchina non trovata")
    return db_machine


@app.post("/plants/create", response_model=schemas.Plant)
def create_plant(plant: schemas.PlantCreate, db: SessionLocal = Depends(get_db),
                 current_user: models.User = Depends(is_admin)):
    return crud.create_plant(db=db, plant=plant)


@app.post("/machines/create")
def create_machine(machine: schemas.MachineCreate, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(is_admin)):
    return crud.create_machine(db=db, machine=machine)


@app.post("/report/create", response_model=schemas.Report)
def create_report(report: schemas.ReportCreate, current_user: models.User = Depends(get_current_user),
                  db: SessionLocal = Depends(get_db)):
    return crud.create_report(db=db, report=report, user_id=current_user.id)


@app.post("/users/create", response_model=schemas.UserRegister)
def create_user(user: schemas.UserCreate, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    if len(user.first_name) == 0 or len(user.last_name) == 0:
        raise HTTPException(status_code=400, detail="I campi non possono essere vuoti")
    return crud.create_user(db=db, user=user)


@app.post("/commissions/create", response_model=schemas.CommissionCreate)
def create_commission(commission: schemas.CommissionCreate, db: SessionLocal = Depends(get_db),
                      current_user: models.User = Depends(is_admin)):
    return crud.create_commission(db=db, commission=commission)


@app.post("/clients/create")
def create_client(client: schemas.ClientCreate, db: SessionLocal = Depends(get_db),
                  current_user: models.User = Depends(is_admin)):
    return crud.create_client(db=db, client=client)


@app.put("/change-password")
def change_password(passwords: models.Password, current_user: schemas.User = Depends(get_current_user),
                    db: SessionLocal = Depends(get_db)):
    return crud.change_password(db=db, user_id=current_user.id, new_password=passwords.new_password,
                                old_password=passwords.old_password)


@app.put("/reset-password")
def reset_password(user_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(is_admin)):
    return crud.reset_password(db=db, user_id=user_id)


@app.put("/report/edit")
def edit_report(report_id: int, report: schemas.ReportCreate, user_id: int, db: SessionLocal = Depends(get_db)):
    return crud.edit_report(db=db, report_id=report_id, report=report, user_id=user_id)


@app.put("/client/edit")
def edit_client(client_id: int, client: schemas.ClientCreate, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    return crud.edit_client(db=db, client_id=client_id, client=client)


@app.put("/commission/edit")
def edit_commission(commission_id: int, commission: schemas.CommissionCreate, db: SessionLocal = Depends(get_db),
                    current_user: models.User = Depends(is_admin)):
    return crud.edit_commission(db=db, commission_id=commission_id, commission=commission)


@app.put("/commission/close")
def close_commission(commission_id: int, db: SessionLocal = Depends(get_db),
                     current_user: models.User = Depends(is_admin)):
    return crud.close_commission(db=db, commission_id=commission_id)


@app.put("/plant/edit")
def edit_plant(plant_id: int, plant: schemas.PlantCreate, db: SessionLocal = Depends(get_db),
               current_user: models.User = Depends(is_admin)):
    return crud.edit_plant(db=db, plant_id=plant_id, plant=plant)


@app.put("/machine/edit")
def edit_machine(machine_id: int, machine: schemas.MachineCreate, db: SessionLocal = Depends(get_db),
                 current_user: models.User = Depends(is_admin)):
    return crud.edit_machine(db=db, machine_id=machine_id, machine=machine)


@app.put("/user/edit")
def edit_user(user_id: int, user: schemas.UserUpdate, db: SessionLocal = Depends(get_db)):
    return crud.edit_user(db=db, user=user, user_id=user_id)


@app.delete("/report/delete")
def delete_report(report_id: int, db: SessionLocal = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    return crud.delete_report(db=db, report_id=report_id, user_id=current_user.id)


@app.delete("/users/delete")
def delete_user(user_id: int, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    return crud.delete_user(db=db, user_id=user_id, current_user_id=current_user.id)


@app.delete("/clients/delete")
def delete_client(client_id: int, db: SessionLocal = Depends(get_db),
                  current_user: models.User = Depends(is_admin)):
    return crud.delete_client(db=db, client_id=client_id)


@app.delete("/commissions/delete")
def delete_commission(commission_id: int, db: SessionLocal = Depends(get_db),
                      current_user: models.User = Depends(is_admin)):
    return crud.delete_commission(db=db, commission_id=commission_id)


@app.delete("/plants/delete")
def delete_plants(plant_id: int, db: SessionLocal = Depends(get_db),
                  current_user: models.User = Depends(is_admin)):
    return crud.delete_plant(db=db, plant_id=plant_id)


@app.delete("/machines/delete")
def delete_machine(machine_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(is_admin)):
    return crud.delete_machine(db=db, machine_id=machine_id)


@app.post("/upload-xml")
def upload_xml(file: UploadFile):
    if file.filename.endswith('.xml') or file.filename.endswith('.XML'):
        try:
            xml = xmltodict.parse(file.file)
            xml = list(xml.values())[0]
            info1 = xml['FatturaElettronicaHeader']['CedentePrestatore']
            info2 = xml['FatturaElettronicaBody']['DatiBeniServizi']['DatiRiepilogo']
            general_info = xml['FatturaElettronicaBody']['DatiGenerali']['DatiGeneraliDocumento']
            parsed = xml['FatturaElettronicaBody']['DatiBeniServizi']['DettaglioLinee']
            with open('app/test.csv', 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=';')
                csvwriter.writerow(['Data documento', general_info['Data']])
                csvwriter.writerow(['Numero documento', general_info['Numero']])
                csvwriter.writerow(['Tipologia documento', general_info['TipoDocumento']])
                csvwriter.writerow(['Identificativo fiscale',
                                    info1['DatiAnagrafici']['IdFiscaleIVA']['IdPaese'] +
                                    info1['DatiAnagrafici']['IdFiscaleIVA']['IdCodice']])
                csvwriter.writerow(['Codice fiscale', info1['DatiAnagrafici']['IdFiscaleIVA']['IdCodice']])
                csvwriter.writerow(['Denominazione', info1['DatiAnagrafici']['Anagrafica']['Denominazione']])
                csvwriter.writerow(['Regime fiscale', info1['DatiAnagrafici']['RegimeFiscale']])
                csvwriter.writerow(['Indirizzo', info1.get('Sede', {}).get('Indirizzo', None)])
                if info1.get('Sede', {}).get('Provincia', None):
                    csvwriter.writerow(['Comune',
                                        info1.get('Sede', {}).get('Comune', None) + ' (' + info1.get('Sede', {}).get(
                                            'Provincia', None) + ')'])
                else:
                    csvwriter.writerow(['Comune', info1.get('Sede', {}).get('Comune', None)])
                csvwriter.writerow(['CAP', info1.get('Sede', {}).get('CAP', None)])
                csvwriter.writerow(['Nazione', info1.get('Sede', {}).get('Nazione', None)])
                csvwriter.writerow([''])
                csvwriter.writerow(
                    ['Codice', 'Descrizione', 'Quantità', 'Prezzo unitario', 'Unità di misura', 'Sconto', 'IVA',
                     'Totale'])
                if type(parsed) == list:
                    for line in parsed:
                        if not line.get('CodiceArticolo', None):
                            full_code = ''
                        else:
                            full_code = ''
                            if type(line['CodiceArticolo']) == list:
                                for value in line['CodiceArticolo']:
                                    full_code += value['CodiceValore'] + '\r(' + value['CodiceTipo'] + ')\r'
                            else:
                                full_code = line['CodiceArticolo']['CodiceValore'] + '\r(' + \
                                            line['CodiceArticolo']['CodiceTipo'] + ')'
                        quantity = line.get('Quantita', None).replace('.', ',') if line.get('Quantita') else None
                        if type(line.get('ScontoMaggiorazione', {})) == list:
                            discount = ''
                            for value in line['ScontoMaggiorazione']:
                                discount += value['Percentuale'].replace('.', ',') + '\r'
                        else:
                            discount = line.get('ScontoMaggiorazione', {}).get('Percentuale', None).replace('.',
                                                                                                            ',') if line.get(
                                'ScontoMaggiorazione', {}).get('Percentuale', None) else None
                        csvwriter.writerow(
                            [full_code,
                             line['Descrizione'], quantity,
                             line['PrezzoUnitario'].replace('.', ','),
                             line.get('UnitaMisura', None), discount,
                             line['AliquotaIVA'].replace('.', ','),
                             line['PrezzoTotale'].replace('.', ',')])
                else:
                    if not parsed.get('CodiceArticolo', None):
                        full_code = ''
                    else:
                        full_code = parsed['CodiceArticolo']['CodiceValore'] + '\r(' + parsed['CodiceArticolo'][
                            'CodiceTipo'] + ')'
                    quantity = parsed.get('Quantita', None).replace('.', ',') if parsed.get('Quantita') else None
                    discount = (
                        parsed.get('ScontoMaggiorazione', {}).get('Percentuale', None).replace('.', ',') if parsed.get(
                            'ScontoMaggiorazione', {}).get('Percentuale', None) is not None else None)
                    csvwriter.writerow(
                        [full_code,
                         parsed['Descrizione'], quantity,
                         parsed['PrezzoUnitario'].replace('.', ','),
                         parsed.get('UnitaMisura', None),
                         discount,
                         parsed['AliquotaIVA'].replace('.', ','),
                         parsed['PrezzoTotale'].replace('.', ',')])
                csvwriter.writerow([''])
                if type(info2) == list:
                    for value in info2:
                        csvwriter.writerow(['Aliquota IVA', value['AliquotaIVA'].replace('.', ',')])
                        csvwriter.writerow(['Totale imponibile', value['ImponibileImporto'].replace('.', ',')])
                        csvwriter.writerow(['Totale imposta', value['Imposta'].replace('.', ',')])
                        csvwriter.writerow(['', ''])
                else:
                    csvwriter.writerow(['Aliquota IVA', info2['AliquotaIVA'].replace('.', ',')])
                    csvwriter.writerow(['Totale imponibile', info2['ImponibileImporto'].replace('.', ',')])
                    csvwriter.writerow(['Totale imposta', info2['Imposta'].replace('.', ',')])
                    csvwriter.writerow(['', ''])
                csvwriter.writerow(['Totale documento', general_info['ImportoTotaleDocumento'].replace('.', ',')])
                if xml['FatturaElettronicaBody'].get('DatiPagamento', {}).get('ModalitaPagamento', None):
                    payment_info = xml['FatturaElettronicaBody']['DatiPagamento']
                    csvwriter.writerow(['Modalità di pagamento', payment_info['ModalitaPagamento']])
                    csvwriter.writerow(['Data di scadenza', payment_info['DataScadenzaPagamento']])
            return FileResponse('app/test.csv', filename=file.filename + '.csv')
        except Exception:
            raise HTTPException(status_code=400, detail='Errore')
    else:
        raise HTTPException(status_code=400, detail='Errore')


@app.post("/send-email")
async def send_in_background(report_id: int,
                             background_tasks: BackgroundTasks,
                             email: EmailStr = Form(...),
                             file: UploadFile = File(...),
                             current_user: models.User = Depends(is_admin),
                             db: SessionLocal = Depends(get_db)) -> Response:
    report = crud.get_report_by_id(db=db, report_id=report_id)
    message = MessageSchema(
        subject=report.last_name.upper() + ' ' + report.first_name.upper() + ' - Intervento ' + report.client_name + ' ' + report.Report.date.strftime(
            '%d/%m/%Y'),
        recipients=[email],
        body='<div style="padding-bottom: 20px;">Buongiorno,<br> in allegato l\'intervento di ' + report.last_name.upper() + ' '
             + report.first_name.upper() + ' in data ' + report.Report.date.strftime(
            '%d/%m/%Y') + ' presso ' + report.client_name + '.<br><br>'
                                                            'Il presente intervento è da ritenersi accettato se '
                                                            'non vi saranno comunicazioni entro 3 giorni '
                                                            'lavorativi.<br><br>' +
             'Cordiali saluti<br>Team Manutenzione</div><hr style="width: 50%; margin-left: 0;">'
             '<div><img src="cid:logo" alt="Move Automation" style="width: 150px; height: auto; padding-top: 20px;"'
             '></div><div>'
             '<a href="www.moveautomation.it">www.moveautomation.it</a><br>'
             'Move Automation S.r.l.<br>'
             'Via Fornaci, 70<br>'
             '38068 Rovereto (TN)<br>'
             '+39.348.2355393</div>',
        subtype=MessageType.html,
        attachments=[file,
                     {
                         "file": "app/static/logo.png",
                         "headers": {"Content-ID": "<logo>",
                                     "Content-Disposition": "inline; filename=\"logo.png\""},
                         "mime_type": "image",
                         "mime_subtype": "png",
                     }]
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    crud.edit_report_email_date(db=db, report_id=report_id, email_date=datetime.datetime.now(ZoneInfo("Europe/Rome")))
    return Response(status_code=200)
