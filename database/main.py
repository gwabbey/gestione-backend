from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .crud import get_joined_tables
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/users/", response_model=list[schemas.User])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)


@app.get("/clients/", response_model=list[schemas.Client])
def read_clients(db: Session = Depends(get_db)):
    return crud.get_clients(db)


@app.post("/users/", response_model=schemas.UserCreate)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_full_name(db, first_name=user.first_name, last_name=user.last_name)
    if len(user.first_name) == 0 or len(user.last_name) == 0:
        raise HTTPException(status_code=400, detail="fields cannot be empty")
    if db_user:
        raise HTTPException(status_code=400, detail="message already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return db_user


@app.get("/joined_tables")
def joined_tables():
    result = get_joined_tables()
    return result
