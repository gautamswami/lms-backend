from typing import Optional, List

from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role_name: str
    counselor_id: Optional[int]


class UserDisplay(UserBase):
    id: int
    counselor: Optional[UserBase]
    total_training_hours: (
        int  # Add total training hours to match ORM and requirement document
    )

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    dp_file_id: str
    password: str
    employee_id: str
    designation: str
    service_line_id: int
    counselor_id: Optional[int]
    entity: str


class UserUpdate(BaseModel):
    # Changed to Optional if updating isn't mandatory
    email: str
    dp_file_id: Optional[str] = None
    designation: Optional[str] = None
    service_line_id: Optional[int] = None
    compliance_hours: Optional[int] = (
        None  # Added to update the compliance hours per user
    )

    class Config:
        from_attributes = True


# ############################################ USER ENDS HERE ####################################################


class ContentBase(BaseModel):
    chapter_id: int


class ContentCreate(ContentBase):
    pass


class ContentDisplay(ContentBase):
    id: int
    title: str
    content_type: str
    file_id: str


class ChapterBase(BaseModel):
    title: str
    description: str
    course_id: int


class ChapterCreate(ChapterBase):
    pass


class ChapterDisplay(ChapterCreate):
    id: int
    contents: list[ContentDisplay]

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    title: str
    description: str
    category: str  # Assuming thumbnail is stored as a URL or file path
    expected_time_to_complete: int
    difficulty_level: Optional[str]  # Added to reflect the course difficulty level
    tags: Optional[str]  # Added to handle course tagging feature


class CourseDisplay(CourseCreate):
    id: int
    thumbnail_file_id: Optional[str]
    service_line_id: Optional[int]
    status: str
    ratings: float
    creation_date: datetime
    approver: Optional[UserDisplay]
    approved_date: Optional[datetime]
    chapters: List[ChapterDisplay] = []

    class Config:
        from_attributes = True


# ############################################ Course ENDS HERE ####################################################


# Admin specific views
class AdminCourseView(CourseDisplay):
    # Includes everything from CourseDisplay and additional admin-specific fields
    created_by: UserDisplay  # Display the creator of the course
    entity: str  # Entity information to which the course belongs

    class Config:
        orm_mode = True


class AdminUserView(UserDisplay):
    # Detailed view for admin to manage user details
    compliance_hours: int
    entity: str
    service_line: str

    class Config:
        orm_mode = True


# Instructor specific views
class InstructorCourseView(CourseDisplay):
    # Similar to AdminCourseView but tailored for instructors
    participants: List[UserDisplay]  # List of participants enrolled in the course

    class Config:
        orm_mode = True


class InstructorUserView(UserDisplay):
    # View for instructors to see user details in their courses
    compliance_hours: (
        int  # Instructors need to track compliance hours for their students
    )

    class Config:
        orm_mode = True


# Trainee specific views
class TraineeCourseView(CourseDisplay):
    # Trainees see a simpler view of the course
    progress: float  # Percentage of course completion

    class Config:
        orm_mode = True


class TraineeProfileView(UserDisplay):
    # Specific view for trainees that includes personal progress and assigned counselor
    total_training_hours: int
    counselor: UserDisplay  # Display the assigned counselor's details

    class Config:
        orm_mode = True


# Learning Path Models for assigning and displaying learning paths
class LearningPathBase(BaseModel):
    name: str
    expiry_date: Optional[datetime]  # Date when the learning path expires


class LearningPathDisplay(LearningPathBase):
    id: int
    courses: List[CourseDisplay]  # List of courses in the learning path

    class Config:
        orm_mode = True


class AssignLearningPath(BaseModel):
    learning_path_id: int
    user_id: int
    assign_date: datetime  # Date when the learning path is assigned to the user

    class Config:
        orm_mode = True


# Feedback Models
class FeedbackCreate(BaseModel):
    course_id: int
    user_id: int
    rating: int
    description: str

    class Config:
        orm_mode = True


class FeedbackDisplay(FeedbackCreate):
    id: int  # Feedback identifier

    class Config:
        orm_mode = True


########


class EnrollmentRequest(BaseModel):
    course_id: int
    user_ids: list[int]  # List of user IDs to enroll

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_details: UserDisplay


class TokenData(BaseModel):
    username: str = None
