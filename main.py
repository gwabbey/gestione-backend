import os
from dotenv import load_dotenv
from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.middleware.cors import CORSMiddleware

import crud
import models
import schemas
from auth import create_access_token, get_current_active_user, get_current_user, is_admin
from database import SessionLocal, engine, get_db

load_dotenv()
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS"))

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def ok():
    return {"message": "ok"}


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


@app.get("/users/", response_model=list[schemas.User])
def read_users(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(is_admin)):
    return crud.users


@app.get("/clients/", response_model=list[schemas.Client])
def get_clients(db: SessionLocal = Depends(get_db)):
    return crud.clients


@app.get("/sites/", response_model=list[schemas.Site])
def get_sites(db: SessionLocal = Depends(get_db)):
    return crud.sites


@app.get("/intervention_types/", response_model=list[schemas.InterventionType])
def get_intervention_types(db: SessionLocal = Depends(get_db)):
    return crud.intervention_types


@app.post("/users/", response_model=schemas.UserCreate)
def create_user(user: schemas.UserCreate, db: SessionLocal = Depends(get_db),
                current_user: models.User = Depends(is_admin)):
    if len(user.first_name) == 0 or len(user.last_name) == 0:
        raise HTTPException(status_code=400, detail="fields cannot be empty")
    return crud.create_user(db=db, user=user)


@app.get("/user/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: SessionLocal = Depends(get_db),
              current_user: models.User = Depends(get_current_active_user)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return db_user


@app.post("/work", response_model=schemas.Work)
def create_activity(work: schemas.Work, current_user: models.User = Depends(get_current_user),
                    db: SessionLocal = Depends(get_db)):
    return crud.create_activity(db=db, work=work, current_user=current_user)


@app.get("/work")
def get_work(current_user: models.User = Depends(is_admin), db: SessionLocal = Depends(get_db)):
    return crud.get_work_table(db)


@app.get("/users/me/", response_model=schemas.User)
async def read_profile(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/work/", response_model=List[schemas.Work])
def read_works(db: SessionLocal = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_works_by_user_id(db=db, user_id=current_user.id)
