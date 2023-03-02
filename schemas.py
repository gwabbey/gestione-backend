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
    password: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    username: str
    role: str

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
    client: str
    site: str
    description: str
    notes: str
    trip_kms: str
    cost: str

    class Config:
        orm_mode = True


class Client(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class Site(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class InterventionType(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
