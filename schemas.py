from __future__ import annotations

from datetime import date
from datetime import datetime
from typing import Optional, List, Union, Dict, Any

from pydantic import BaseModel, EmailStr, Field
from fastapi import UploadFile


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


class UserTeamView(UserBase):
    number_of_trainings_completed: int
    hours_of_training_completed: int
    number_of_trainings_pending: int
    number_of_mandatory_trainings_overdue: int
    hours_of_non_technical_training_completed:int
    hours_of_technical_training_completed:int
    hours_of_technical_training_target:int
    hours_of_non_technical_training_target:int

    compliance_status: str
    reminder_needed: bool


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


class ContentCreate(BaseModel_):
    titles_json: str = Field(..., description="JSON-encoded list of titles")


class ContentFile(BaseModel_):
    title: str = Field(..., description="The title of the content")
    file: UploadFile = Field(..., description="The file to upload")


# class ContentCreate(ContentBase):
#     pass


class ContentDisplay(ContentBase):
    id: int
    title: str
    content_type: str
    file_id: str


class QuestionBase(BaseModel_):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class QuestionCreate(QuestionBase):
    correct_answer: str


class QuestionDisplay(QuestionBase):
    id: str


class QuestionGetRequest(BaseModel_):
    course_id: List[int] = []
    chapter_id: List[int] = []


class QuestionUpdate(QuestionBase):
    question: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    course_id: Optional[int] = None


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
    entity: Optional[str]  # Added to handle course tagging feature
    service_line_id: Optional[str]
    chapters: List[ChapterCreate] = Field(default_factory=list)


class CourseSortDisplay(CourseCreate):
    id: int
    thumbnail_file_id: Optional[str]
    service_line_id: Optional[str]
    status: str
    ratings: float
    creation_date: datetime
    approved_date: Optional[datetime]
    chapters_count: Optional[int]
    feedback_count: Optional[int]
    completed_students_count: Optional[int]
    average_rating: Optional[int]


class CourseFullDisplay(CourseSortDisplay):
    approver: Optional[UserDisplay]
    creator: Optional[UserDisplay]
    chapters: List[ChapterDisplay] = []

    class Config:
        from_attributes = True


class CourseUpdate(CourseCreate):
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    expected_time_to_complete: Optional[int]
    difficulty_level: Optional[str]
    tags: Optional[str]
    entity: Optional[str]
    service_line_id: Optional[str]


# ############################################ Course ENDS HERE ####################################################


class DashStats(BaseModel_):
    numeric_stats: Dict[str, Any]
    details: Dict[str, Any]


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
    name: str = Field(..., description="The name of the learning path")
    entity: str = Field(
        None, description="The entity associated with the learning path"
    )
    service_line_id: str = Field(
        ..., description="The service line ID associated with the learning path"
    )


class LearningPathCreate(LearningPathBase):
    course_ids: List[int] = Field(
        ..., description="List of course IDs included in the learning path"
    )


class LearningPathUpdate(LearningPathBase):
    # complete this too
    course_ids: List[int] = Field(
        None,
        description="List of course IDs included in the learning path, optional for updates",
    )


class LearningPathDisplay(LearningPathBase):
    id: int
    courses: List[CourseSortDisplay]  # List of courses in the learning path

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
    course_id: Optional[int]
    learning_path_id: Optional[int]
    user_ids: list[int]  # List of user IDs to enroll

    class Config:
        from_attributes = True


class Token(BaseModel_):
    access_token: str
    token_type: str
    user_details: Union[UserDisplay, InstructorDisplay]


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
    admins: List[UserDisplay]
    designations: List[DesignationModel]
    service_lines: List[ServiceLineModel]
    external_roles: List[ExternalRoleModel]
    internal_roles: List[InternalRoleModel]
    entities: list[str] = ["Pierian", "entity2"]

    class Config:
        from_attributes = True


class ResetPassword(BaseModel_):
    email: str
    otp: str
    new_password: str

    class Config:
        from_attributes = True


class DashInput(BaseModel_):
    email: str

    class Config:
        from_attributes = True


# ======================================FEEDBACK======================================


class FeedbackCreate(BaseModel_):
    user_id: Optional[int] = None
    course_id: Optional[int] = None
    description: str
    rating: int


class FeedbackDisplay(BaseModel_):
    id: int
    user_id: Optional[int]
    course_id: Optional[int]
    description: str
    rating: int
    created_at: datetime
    submitter: UserBase
    course: CourseSortDisplay

    class Config:
        from_attributes = True


class CertificationFilter(BaseModel_):
    category: Optional[str] = Field(
        None, description="Filter by the category of the certification"
    )
    uploaded_by_id: Optional[int] = Field(
        None, description="Filter by the user ID who uploaded the certification"
    )


# ======================================ExternalCertification======================================


class ExternalCertificationCreate(BaseModel_):
    course_name: str
    category: str
    date_of_completion: date
    hours: int
    certificate_provider: str
    file_id: str


class ExternalCertificationUpdate(BaseModel_):
    course_name: Optional[str]
    category: Optional[str]
    date_of_completion: Optional[date]
    hours: Optional[int]
    certificate_provider: Optional[str]
    file_id: Optional[str]


class ExternalCertificationDisplay(BaseModel_):
    id: int
    course_name: str
    category: str
    date_of_completion: date
    hours: int
    file_id: str
    certificate_provider: str
    uploaded_by_id: int
    status: str

    class Config:
        from_attributes = True
