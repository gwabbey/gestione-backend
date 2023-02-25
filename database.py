from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = "postgresql://postgres:gab@localhost:5432/postgres?application_name=gestione"

engine = create_engine(DATABASE_URL, pool_recycle=3600)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
