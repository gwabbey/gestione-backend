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


class Work(BaseModel):
    date: datetime.date
    intervention_duration: datetime.time
    intervention_type: str
    intervention_location: str
    site_id: int
    supervisor: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    trip_kms: Optional[str] = None
    cost: Optional[str] = None
    date_created: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class WorkDelete(BaseModel):
    id: int

    class Config:
        orm_mode = True


class Client(BaseModel):
    id: int
    name: str
    city: str
    address: str
    email: Optional[str] = None
    contact: Optional[str] = None
    phone_number: Optional[str] = None
    date_created: Optional[datetime.datetime] = None


class ClientCreate(BaseModel):
    name: str
    city: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    phone_number: Optional[str] = None
    date_created: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class Site(BaseModel):
    id: int
    date_created: Optional[datetime.datetime] = None
    code: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[int] = None

    class Config:
        orm_mode = True


class SiteCreate(BaseModel):
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
