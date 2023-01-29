from pydantic import BaseModel


class UserBase(BaseModel):
    name: str
    message: str


class UserCreate(UserBase):
    name: str
    message: str


class User(UserBase):
    id: int
    name: str
    message: str

    class Config:
        orm_mode = True
