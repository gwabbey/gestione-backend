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


class ClientCreate(BaseModel):
    name: str


class Client(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
