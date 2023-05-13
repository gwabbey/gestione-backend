import datetime
import os
from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jinja2 import Template
from pydantic import BaseSettings
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from weasyprint import HTML

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.auth import create_access_token, get_current_active_user, get_current_user, is_admin
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


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users", response_model=list[schemas.User])
def get_users(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(is_admin)):
    return db.query(models.User).order_by(models.User.id).all()


@app.get("/clients", response_model=list[schemas.Client])
def get_clients(db: SessionLocal = Depends(get_db)):
    return db.query(models.Client).order_by(models.Client.id).all()


@app.get("/commissions")
def get_commissions(db: SessionLocal = Depends(get_db), client_id: Optional[int] = None, user_id: Optional[int] = None):
    if client_id:
        return crud.get_commissions(db, client_id=client_id)
    elif user_id:
        return crud.get_user_commissions(db, user_id=user_id)
    return crud.get_commissions(db)


@app.get("/roles", response_model=list[schemas.Role])
def get_roles(db: SessionLocal = Depends(get_db)):
    roles = db.query(models.Role).order_by(models.Role.id).all()
    return roles


@app.get("/intervention_types", response_model=list[schemas.InterventionType])
def get_intervention_types(db: SessionLocal = Depends(get_db)):
    intervention_types = db.query(models.InterventionType).order_by(models.InterventionType.id).all()
    return intervention_types


@app.get("/locations", response_model=list[schemas.Location])
def get_locations(db: SessionLocal = Depends(get_db)):
    locations = db.query(models.Location).order_by(models.Location.id).all()
    return locations


@app.get("/plants")
def get_plants(db: SessionLocal = Depends(get_db)):
    plants = db.query(models.Plant).order_by(models.Plant.id).all()
    return plants


@app.get("/machines")
def get_machines(db: SessionLocal = Depends(get_db)):
    return crud.get_machines(db)


@app.get("/reports")
def get_reports(current_user: models.User = Depends(is_admin),
                db: SessionLocal = Depends(get_db)):
    return crud.get_reports(db)


@app.get("/months")
def get_months(db: SessionLocal = Depends(get_db)):
    return crud.get_months(db)


@app.get("/plant")
def get_plant_by_client(db: SessionLocal = Depends(get_db), client_id: int = None):
    return crud.get_plant_by_client(db, client_id=client_id)


@app.get("/machine")
def get_machine_by_plant(db: SessionLocal = Depends(get_db), plant_id: int = None):
    return crud.get_machine_by_plant(db, plant_id=plant_id)


@app.get("/me/months")
def get_my_months(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user),
                  work_id: Optional[int] = None):
    return crud.get_months(db, user_id=current_user.id, work_id=work_id)


@app.get("/reports/monthly")
def get_reports_in_month(month: Optional[str] = None, db: SessionLocal = Depends(get_db)):
    return crud.get_reports_in_month(month=month, db=db)


@app.get("/reports/interval")
def get_reports_in_interval(start_date: Optional[str] = None, end_date: Optional[str] = None,
                            db: SessionLocal = Depends(get_db)):
    return crud.get_reports_in_interval(start_date=start_date, end_date=end_date, db=db)


@app.get("/me/reports/monthly")
def get_my_reports_in_month(month: Optional[str] = None,
                            current_user: models.User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    return crud.get_reports_in_month(month=month, user_id=current_user.id, db=db)


@app.get("/me/reports/interval")
def get_my_interval_report(start_date: Optional[str] = None, end_date: Optional[str] = None,
                           work_id: Optional[int] = None,
                           current_user: models.User = Depends(get_current_user),
                           db: SessionLocal = Depends(get_db)):
    return crud.get_interval_report(start_date=start_date, end_date=end_date, work_id=work_id,
                                    operator_id=current_user.id,
                                    db=db)


@app.get("/report/{report_id}")
def get_report_by_id(report_id: int, db: SessionLocal = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    report = crud.get_report_by_id(db, report_id=report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Intervento non trovato")
    if db.query(models.Report).filter(
            models.Report.id == report_id).first().operator_id != current_user.id and current_user.role != 'admin':
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
    date = datetime.datetime.now()
    template.globals['now'] = date.strftime
    rendered_html = template.render(report=report)
    pdf = HTML(string=rendered_html).write_pdf()
    return Response(content=pdf, media_type="application/pdf")


@app.get("/me", response_model=schemas.User)
async def get_profile(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.get("/me/reports")
def get_my_reports(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_reports(db=db, user_id=current_user.id)


@app.get("/me/commissions")
def get_user_commissions(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user),
                         client_id: int = None):
    return crud.get_commissions(db=db, client_id=client_id)


@app.get("/user/{user_id}", response_model=schemas.User)
def get_user_by_id(user_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(is_admin)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return db_user


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


@app.put("/change_password")
def change_password(user_id: int, password: str, db: SessionLocal = Depends(get_db),
                    current_user: models.User = Depends(is_admin)):
    return crud.change_password(db=db, user_id=user_id, password=password)


@app.put("/report/edit")
def edit_report(report_id: int, report: schemas.ReportCreate, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    return crud.edit_report(db=db, report_id=report_id, report=report, user_id=current_user.id)


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
def delete_commissions(work_id: int, db: SessionLocal = Depends(get_db),
                       current_user: models.User = Depends(is_admin)):
    return crud.delete_commission(db=db, work_id=work_id)
