from pydantic import BaseModel, EmailStr


class UserUpdate(BaseModel):
    UserName: str
    Email: EmailStr
    Role: str
    Credits: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class UserBase(BaseModel):
    UserName: str
    Email: str
    Role: str


class UserCreate(UserBase):
    Password: str
    Role: str


class UserInDB(UserBase):
    UserID: int
    Role: str
    Credits: int

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    Email: str
    Password: str
