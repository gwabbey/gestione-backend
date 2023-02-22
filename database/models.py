from sqlalchemy import Column, Integer, String, ForeignKey, Time, Date
from .database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class Operator(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    first_name = Column(String)
    last_name = Column(String)


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String)


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
