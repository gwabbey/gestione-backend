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

app = FastAPI()  # (openapi_url=settings.openapi_url, docs_url=None, redoc_url=None)
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
            detail="Credenziali non valide.",
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


@app.get("/clients")
def get_clients(db: SessionLocal = Depends(get_db)):
    return db.query(models.Client).order_by(models.Client.id).all()


@app.get("/sites")
def get_sites(db: SessionLocal = Depends(get_db), user_id: Optional[int] = None):
    return crud.get_sites(db, user_id)


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


@app.get("/work")
def get_work(current_user: models.User = Depends(is_admin),
             db: SessionLocal = Depends(get_db)):
    return crud.get_work_table(db)


@app.get("/months")
def get_months(db: SessionLocal = Depends(get_db), operator_id: Optional[int] = None,
               site_id: Optional[int] = None):
    return crud.get_months(db, operator_id, site_id)


@app.get("/me/months")
def get_my_months(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user),
                  site_id: Optional[int] = None):
    return crud.get_months(db, operator_id=current_user.id, site_id=site_id)


@app.get("/work/monthly")
def get_monthly_work(month: Optional[str] = None, site_id: Optional[int] = None,
                     operator_id: Optional[int] = None, db: SessionLocal = Depends(get_db)):
    return crud.get_monthly_work(month=month, site_id=site_id, operator_id=operator_id, db=db)


@app.get("/work/interval")
def get_interval_work(start_date: Optional[str] = None, end_date: Optional[str] = None,
                      site_id: Optional[int] = None,
                      operator_id: Optional[int] = None, db: SessionLocal = Depends(get_db)):
    return crud.get_interval_work(start_date=start_date, end_date=end_date, site_id=site_id, operator_id=operator_id,
                                  db=db)


@app.get("/me/work/monthly")
def get_my_monthly_work(month: Optional[str] = None, site_id: Optional[int] = None,
                        current_user: models.User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    return crud.get_monthly_work(month=month, site_id=site_id, operator_id=current_user.id, db=db)


@app.get("/me/work/interval")
def get_my_interval_work(start_date: Optional[str] = None, end_date: Optional[str] = None,
                         site_id: Optional[int] = None,
                         current_user: models.User = Depends(get_current_user),
                         db: SessionLocal = Depends(get_db)):
    return crud.get_interval_work(start_date=start_date, end_date=end_date, site_id=site_id,
                                  operator_id=current_user.id,
                                  db=db)


@app.get("/work/{work_id}")
def get_work_by_id(work_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    if not current_user.id:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a vedere questo intervento.")
    work = crud.get_work_by_id(db, work_id=work_id, user_id=current_user.id)
    if work is None:
        raise HTTPException(status_code=404, detail="Intervento non trovato.")
    return work


@app.get("/work/{work_id}/report")
def get_work_report(work_id: int, db: SessionLocal = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    if not current_user.id:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a vedere questo intervento.")
    work = crud.get_work_by_id(db, work_id=work_id, user_id=1)
    if work is None:
        raise HTTPException(status_code=404, detail="Intervento non trovato.")

    with open('app/result.html') as file:
        template = Template(file.read())

    date = datetime.datetime.now()
    template.globals['now'] = date.strftime

    rendered_html = template.render(work=work)
    pdf = HTML(string=rendered_html).write_pdf()
    return Response(content=pdf, media_type="application/pdf")


@app.get("/me", response_model=schemas.User)
async def get_profile(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.get("/me/work")
def get_user_works(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_works_by_user_id(db=db, user_id=current_user.id)


@app.get("/me/sites")
def get_user_sites(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_sites(db=db, user_id=current_user.id)


@app.get("/user/{user_id}", response_model=schemas.User)
def get_user_by_id(user_id: int, db: SessionLocal = Depends(get_db),
                   current_user: models.User = Depends(is_admin)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    return db_user


@app.post("/work/create", response_model=schemas.Work)
def create_work(work: schemas.Work, current_user: models.User = Depends(get_current_user),
                db: SessionLocal = Depends(get_db)):
    return crud.create_work(db=db, work=work, user_id=current_user.id)


@app.post("/users/create", response_model=schemas.UserRegister)
def create_user(user: schemas.UserCreate, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    if len(user.first_name) == 0 or len(user.last_name) == 0:
        raise HTTPException(status_code=400, detail="I campi non possono essere vuoti.")
    return crud.create_user(db=db, user=user)


@app.post("/sites/create", response_model=schemas.SiteCreate)
def create_site(site: schemas.SiteCreate, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    return crud.create_site(db=db, site=site)


@app.post("/clients/create")
def create_client(client: schemas.ClientCreate, db: SessionLocal = Depends(get_db),
                  current_user: models.User = Depends(is_admin)):
    return crud.create_client(db=db, client=client)


@app.put("/change_password")
def change_password(user_id: int, password: str, db: SessionLocal = Depends(get_db),
                    current_user: models.User = Depends(is_admin)):
    return crud.change_password(db=db, user_id=user_id, password=password)


@app.put("/work/update", response_model=schemas.Work)
def update_work(work_id: int, user_id: int, work: schemas.Work, db: SessionLocal = Depends(get_db)):
    return crud.update_work(db=db, work_id=work_id, work=work, user_id=user_id)


@app.delete("/work/delete")
def delete_work(work_id: int, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    return crud.delete_work(db=db, work_id=work_id, user_id=current_user.id)


@app.delete("/users/delete")
def delete_user(user_id: int, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    return crud.delete_user(db=db, user_id=user_id, current_user_id=current_user.id)


@app.delete("/clients/delete")
def delete_client(client_id: int, db: SessionLocal = Depends(get_db),
                  current_user: models.User = Depends(is_admin)):
    return crud.delete_client(db=db, client_id=client_id)


@app.delete("/sites/delete")
def delete_sites(site_id: int, db: SessionLocal = Depends(get_db),
                 current_user: models.User = Depends(is_admin)):
    return crud.delete_site(db=db, site_id=site_id)
