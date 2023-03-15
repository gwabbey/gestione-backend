from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, DateTime
from sqlalchemy.orm import relationship

from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    temp_password = Column(String)
    phone_number = Column(String)
    role = Column(String)

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password)


class Work(Base):
    __tablename__ = "work"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    operator_id = Column(Integer, ForeignKey("operators.id"))
    date = Column(Date)
    date_created = Column(DateTime)
    intervention_duration = Column(Time)
    intervention_type = Column(String)
    intervention_location = Column(String)
    site_id = Column(Integer, ForeignKey("sites.id"))
    description = Column(String)
    notes = Column(String)
    trip_kms = Column(String)
    cost = Column(String)


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, unique=True, index=True)
    city = Column(String)
    address = Column(String)
    email = Column(String)
    contact = Column(String)
    phone_number = Column(String)
    date_created = Column(DateTime)


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    code = Column(String)
    description = Column(String)
    client_id = Column(Integer, ForeignKey("clients.id"))
    date_created = Column(DateTime)


class InterventionType(Base):
    __tablename__ = "intervention_types"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String)


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String)
