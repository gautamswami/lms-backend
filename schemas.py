from pydantic import BaseModel, EmailStr


class CourseCreate(BaseModel):
    Name: str
    Description: str
    Thumbnail: str  # Assuming thumbnail is stored as a URL or file path


class CourseDisplay(CourseCreate):
    CourseID: int
    InstructorID: int
    DepartmentID: int
    IsApproved: bool
    Rating: float

    class Config:
        orm_mode = True


class ChapterCreate(BaseModel):
    Title: str
    Description: str


class ChapterDisplay(ChapterCreate):
    ChapterID: int
    CourseID: int

    class Config:
        orm_mode = True


class EnrollmentCreate(BaseModel):
    CourseID: int
    EnrollDate: str  # Using ISO format date string


class EnrollmentDisplay(EnrollmentCreate):
    EnrollmentID: int
    UserID: int
    TimeSpent: int  # Time spent in minutes

    class Config:
        orm_mode = True


# Schemas for User related operations (if needed)
class UserBase(BaseModel):
    FirstName: str
    LastName: str
    Email: EmailStr
    RoleName: str


class UserDisplay(UserBase):
    UserID: int

    class Config:
        orm_mode = True


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
