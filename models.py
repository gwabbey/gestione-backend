from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password)


class Work(Base):
    __tablename__ = "work"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"))
    client = Column(String)
    date = Column(Date)
    intervention_duration = Column(Time)
    intervention_type = Column(String)
    intervention_location = Column(String)
    site = Column(String)
    description = Column(String)
    notes = Column(String)
    trip_kms = Column(String)
    cost = Column(String)


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String)


