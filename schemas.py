from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class BaseModel_(BaseModel):
    class Config:
        from_attributes = True


class UserBase(BaseModel_):
    first_name: str
    last_name: str
    email: EmailStr
    role_name: str
    employee_id: str
    designation: str
    service_line_id: str
    external_role_name: str


class UserDisplay(UserBase):
    id: int
    counselor: Optional[UserBase]
    total_training_hours: (
        int  # Add total training hours to match ORM and requirement document
    )
    account_creation_date: datetime

    class Config:
        from_attributes = True


class InstructorDisplay(UserBase):
    id: int
    counselor: Optional[UserBase]
    team_members: Optional[List[UserBase]]
    total_training_hours: (
        int  # Add total training hours to match ORM and requirement document
    )

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    dp_file_id: Optional[str]
    password: str
    counselor_id: Optional[int]
    entity: str


class UserUpdate(BaseModel_):
    # Changed to Optional if updating isn't mandatory
    email: str
    dp_file_id: Optional[str] = None
    designation: Optional[str] = None
    service_line_id: Optional[str] = None
    compliance_hours: Optional[int] = (
        None  # Added to update the compliance hours per user
    )

    class Config:
        from_attributes = True


# ############################################ USER ENDS HERE ####################################################


class ContentBase(BaseModel_):
    chapter_id: int


class ContentCreate(ContentBase):
    pass


class ContentDisplay(ContentBase):
    id: int
    title: str
    content_type: str
    file_id: str


class ChapterBase(BaseModel_):
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


class CourseCreate(BaseModel_):
    title: str
    description: str
    category: str  # Assuming thumbnail is stored as a URL or file path
    expected_time_to_complete: int
    difficulty_level: Optional[str]  # Added to reflect the course difficulty level
    tags: Optional[str]  # Added to handle course tagging feature


class CourseSortDisplay(CourseCreate):
    id: int
    thumbnail_file_id: Optional[str]
    service_line_id: Optional[str]
    status: str
    ratings: float
    creation_date: datetime
    approved_date: Optional[datetime]


class CourseFullDisplay(CourseSortDisplay):
    approver: Optional[UserDisplay]
    chapters: List[ChapterDisplay] = []

    class Config:
        from_attributes = True


# ############################################ Course ENDS HERE ####################################################


class DashStats(BaseModel_):
    enrolled_count: int
    active_count: int
    completed_count: int


class UserDashStats(CourseFullDisplay, DashStats):
    pass


# ############################################ STATS ENDS HERE ####################################################


# Admin specific views
class AdminCourseViewFull(CourseFullDisplay):
    # Includes everything from CourseFullDisplay and additional admin-specific fields
    created_by: UserDisplay  # Display the creator of the course
    entity: str  # Entity information to which the course belongs

    class Config:
        from_attributes = True


class AdminUserView(UserDisplay):
    # Detailed view for admin to manage user details
    compliance_hours: int
    entity: str
    service_line: str

    class Config:
        from_attributes = True


# Instructor specific views
class InstructorCourseViewFull(CourseFullDisplay):
    # Similar to AdminCourseViewFull but tailored for instructors
    participants: List[UserDisplay]  # List of participants enrolled in the course

    class Config:
        from_attributes = True


class InstructorUserView(UserDisplay):
    # View for instructors to see user details in their courses
    compliance_hours: (
        int  # Instructors need to track compliance hours for their students
    )

    class Config:
        from_attributes = True


# Trainee specific views
class TraineeCourseViewFull(CourseFullDisplay):
    # Trainees see a simpler view of the course
    progress: float  # Percentage of course completion

    class Config:
        from_attributes = True


class TraineeProfileView(UserDisplay):
    # Specific view for trainees that includes personal progress and assigned counselor
    total_training_hours: int
    counselor: UserDisplay  # Display the assigned counselor's details

    class Config:
        from_attributes = True


# Learning Path Models for assigning and displaying learning paths
class LearningPathBase(BaseModel_):
    name: str
    expiry_date: Optional[datetime]  # Date when the learning path expires


class LearningPathDisplay(LearningPathBase):
    id: int
    courses: List[CourseFullDisplay]  # List of courses in the learning path

    class Config:
        from_attributes = True


class AssignLearningPath(BaseModel_):
    learning_path_id: int
    user_id: int
    assign_date: datetime  # Date when the learning path is assigned to the user

    class Config:
        from_attributes = True


# Feedback Models
class FeedbackCreate(BaseModel_):
    course_id: int
    user_id: int
    rating: int
    description: str

    class Config:
        from_attributes = True


class FeedbackDisplay(FeedbackCreate):
    id: int  # Feedback identifier

    class Config:
        from_attributes = True


########


class EnrollmentRequest(BaseModel_):
    course_id: int
    user_ids: list[int]  # List of user IDs to enroll

    class Config:
        from_attributes = True


class Token(BaseModel_):
    access_token: str
    token_type: str
    user_details: UserDisplay


class TokenData(BaseModel_):
    username: str = None


# Pydantic models
class ServiceLineModel(BaseModel_):

    name: str

    class Config:
        from_attributes = True


class DesignationModel(BaseModel_):

    name: str

    class Config:
        from_attributes = True


class ExternalRoleModel(BaseModel_):

    name: str

    class Config:
        from_attributes = True


class InternalRoleModel(BaseModel_):

    RoleName: str
    Description: str

    class Config:
        from_attributes = True


class UM_send_all(BaseModel_):
    instructors: List[InstructorDisplay]
    designations: List[DesignationModel]
    service_lines: List[ServiceLineModel]
    external_roles: List[ExternalRoleModel]
    internal_roles: List[InternalRoleModel]
    entities: list[str] = ["Pierian", "entity2"]

    class Config:
        from_attributes = True
