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
        from_attributes = True


class ChapterCreate(BaseModel):
    Title: str
    Description: str


class ChapterDisplay(ChapterCreate):
    ChapterID: int
    CourseID: int

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    CourseID: int
    EnrollDate: str  # Using ISO format date string


class EnrollmentDisplay(EnrollmentCreate):
    EnrollmentID: int
    UserID: int
    TimeSpent: int  # Time spent in minutes

    class Config:
        from_attributes = True


# Schemas for User related operations (if needed)
class UserBase(BaseModel):
    FirstName: str
    LastName: str
    Email: EmailStr
    RoleName: str


class UserDisplay(UserBase):
    UserID: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    dp_file_id: str
    email:str
    designation:str
    role_name:str
    service_line_id:int

    class Config:
        from_attributes = True


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
    dp_file_id: str
    first_name: str
    last_name:str
    email:str
    password:str
    employee_id:str
    designation:str
    role_name:str
    service_line_id:int



class UserInDB(UserBase):
    UserID: int
    Role: str
    Credits: int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    Email: str
    Password: str
