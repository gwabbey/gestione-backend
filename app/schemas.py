import datetime
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

    class Config:
        orm_mode = True


class UserRegister(BaseModel):
    temp_password: Optional[str] = None

    class Config:
        orm_mode = True


class UserUpdate(UserBase):
    pass


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class Report(BaseModel):
    id: int
    operator_id: int
    type: str
    work_id: int
    date: datetime.date
    intervention_duration: datetime.time
    intervention_type: str
    intervention_location: str
    supervisor: str
    description: str
    notes: Optional[str] = None
    trip_kms: Optional[str] = None
    cost: Optional[str] = None
    date_created: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class ReportCreate(BaseModel):
    type: str
    work_id: int
    date: datetime.date
    intervention_duration: datetime.time
    intervention_type: str
    intervention_location: str
    supervisor: str
    description: str
    notes: Optional[str] = None
    trip_kms: Optional[str] = None
    cost: Optional[str] = None
    date_created: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class ReportDelete(BaseModel):
    id: int

    class Config:
        orm_mode = True


class Client(BaseModel):
    id: int
    name: str
    province: str
    city: str
    cap: str
    address: str
    email: str
    contact: str
    phone_number: str
    date_created: datetime.datetime

    class Config:
        orm_mode = True


class ClientCreate(BaseModel):
    name: str
    province: str
    city: str
    cap: str
    address: str
    email: str
    contact: str
    phone_number: str

    class Config:
        orm_mode = True


class Plant(BaseModel):
    id: int
    client_id: int
    name: str
    city: str
    province: str
    cap: str
    address: str
    email: str
    contact: str
    phone_number: str
    date_created: datetime.datetime

    class Config:
        orm_mode = True


class PlantCreate(BaseModel):
    client_id: int
    name: str
    city: str
    province: str
    cap: str
    address: str
    email: str
    contact: str
    phone_number: str

    class Config:
        orm_mode = True


class Machine(BaseModel):
    id: int
    plant_id: int
    robotic_island: str
    code: str
    name: str
    brand: str
    model: str
    serial_number: str
    production_year: str
    cost_center: str
    description: str
    date_created: datetime.datetime


class MachineCreate(BaseModel):
    plant_id: int
    robotic_island: str
    code: str
    name: str
    brand: str
    model: str
    serial_number: str
    production_year: str
    cost_center: str
    description: str


class Commission(BaseModel):
    id: int
    code: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[int] = None
    date_created: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class CommissionCreate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[int] = None

    class Config:
        orm_mode = True


class InterventionType(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class Location(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class Role(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
