import datetime
import enum

from pydantic import BaseModel


class UserCreate(BaseModel):
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class User(BaseModel):
    id: int
    first_name: str
    last_name: str

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
    operator_id: int

    class Config:
        orm_mode = True
