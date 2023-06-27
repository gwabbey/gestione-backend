from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime

from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    temp_password = Column(String)
    phone_number = Column(String)

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password)


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, unique=True, index=True)
    province = Column(String)
    city = Column(String)
    cap = Column(String)
    address = Column(String)
    email = Column(String)
    contact = Column(String)
    phone_number = Column(String)
    date_created = Column(DateTime)


class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    name = Column(String)
    city = Column(String)
    province = Column(String)
    cap = Column(String)
    address = Column(String)
    email = Column(String)
    contact = Column(String)
    phone_number = Column(String)
    date_created = Column(DateTime)


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    robotic_island = Column(String)
    code = Column(String)
    name = Column(String)
    brand = Column(String)
    model = Column(String)
    serial_number = Column(String)
    production_year = Column(String)
    cost_center = Column(String)
    description = Column(String)
    date_created = Column(DateTime)


class Commission(Base):
    __tablename__ = "commissions"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    code = Column(String)
    description = Column(String)
    status = Column(String)
    date_created = Column(DateTime)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    operator_id = Column(Integer, ForeignKey("operators.id"))
    work_id = Column(Integer)  # might be either a machine or a commission
    type = Column(String)  # either machine or commission
    date = Column(Date)
    intervention_duration = Column(String)
    intervention_type = Column(String)
    intervention_location = Column(String)
    supervisor_id = Column(Integer, ForeignKey("operators.id"))
    description = Column(String)
    notes = Column(String)
    trip_kms = Column(String)
    cost = Column(String)
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


class Password(BaseModel):
    old_password: str
    new_password: str
