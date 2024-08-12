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
    dp_file_id: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    role_name: str
    employee_id: str
    designation: str
    service_line_id: str
    external_role_name: Optional[str]
    entity: Optional[Any]


class UserSortDisplay(UserBase):
    id: int


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
    team_members: Optional[List[UserBase]] = []
    total_training_hours: (
        int  # Add total training hours to match ORM and requirement document
    )

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    dp_file_id: Optional[str]
    password: str
    counselor_id: Optional[int]
    entity: str = "PIERAG"


class UserUpdate(BaseModel_):
    # Changed to Optional if updating isn't mandatory
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_name: Optional[str] = None
    employee_id: Optional[str] = None
    external_role_name: Optional[str] = None
    dp_file_id: Optional[str] = None
    designation: Optional[str] = None
    service_line_id: Optional[str] = None
    counselor_id: Optional[int] = None
    entity: Optional[str] = None


class UserTeamView(UserSortDisplay):
    number_of_trainings_completed: Optional[int]
    hours_of_training_completed: Optional[int]
    number_of_trainings_pending: Optional[int]
    number_of_mandatory_trainings_overdue: Optional[int]
    hours_of_non_technical_training_completed: Optional[int]
    hours_of_technical_training_completed: Optional[int]
    hours_of_technical_training_target: Optional[int]
    hours_of_non_technical_training_target: Optional[int]
    total_tech_enrolled_hours: Optional[int]
    total_non_tech_enrolled_hours: Optional[int]

    compliance_status: Optional[str]
    reminder_needed: Optional[bool]


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
    file_id: Optional[str]
    expected_time_to_complete: Optional[Union[int, float]] = 0


class QuestionBase(BaseModel_):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class QuestionCreate(QuestionBase):
    correct_answer: str


class QuestionDisplay(QuestionBase):
    id: int


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
    id: Optional[int] = None


class QuestionAddToChapter(BaseModel_):
    question_list: List[QuestionCreate]
    question_ids: List[int]


class ChapterBase(BaseModel_):
    title: str
    description: str
    course_id: int


class ChapterCreate(ChapterBase):
    pass


class ChapterDisplay(ChapterCreate):
    id: int
    expected_time_to_complete: Optional[Union[int, float]] = 0
    contents: list[ContentDisplay]
    questions: list[QuestionDisplay]

    class Config:
        from_attributes = True


class CourseBase(BaseModel_):
    title: str
    category: str  # Assuming thumbnail is stored as a URL or file path
    expected_time_to_complete: Optional[Union[int, float]] = 0
    difficulty_level: Optional[str]  # Added to reflect the course difficulty level
    tags: Optional[str]  # Added to handle course tagging feature
    entity: Optional[str] = "PIERAG"  # Added to handle course tagging feature
    service_line_id: Optional[str]


class CourseCreate(CourseBase):
    description: str
    chapters: List[ChapterCreate] = Field(default_factory=list)


class CourseSortDisplay(CourseBase):
    id: int
    thumbnail_file_id: Optional[str]
    status: str
    ratings: float
    creation_date: datetime
    approved_date: Optional[datetime]
    chapters_count: Optional[int]
    feedback_count: Optional[int]
    completed_students_count: Optional[int]
    expected_time_to_complete: Optional[Union[int, float]] = 0
    average_rating: Optional[float]
    is_enrolled: Optional[bool] = False
    creator: Optional[UserDisplay]


class CourseFullDisplay(CourseSortDisplay):
    description: Optional[str]
    approver: Optional[UserDisplay]
    chapters: List[ChapterDisplay] = []
    questions: List[QuestionDisplay] = []

    class Config:
        from_attributes = True


class ContentUpdate(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    content_type: Optional[str] = None  # e.g., "video", "quiz", "text"
    file_id: Optional[str] = None  # Link to the associated file
    expected_time_to_complete: Optional[int] = None


class ChapterUpdate(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    contents: Optional[List[ContentUpdate]] = None
    questions: Optional[List[QuestionUpdate]] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    expected_time_to_complete: Optional[Union[int, float]] = 0
    difficulty_level: Optional[str] = None
    tags: Optional[str] = None
    entity: Optional[str] = None
    service_line_id: Optional[str] = None
    chapters: Optional[List[ChapterUpdate]] = None
    questions: Optional[List[QuestionUpdate]] = None


class EnrolledCourseDisplay(CourseFullDisplay):
    completed_hours: Optional[Union[int, float]] = Field(
        None, description="Total hours completed by the user in the course"
    )
    completion_percentage: Optional[Union[int, float]] = Field(
        None, description="Percentage of the course completed by the user"
    )


class ListCoursesDisplay(EnrolledCourseDisplay):
    total_questions: Optional[int] = 0  # Total number of questions in the course
    completed_questions: Optional[int] = (
        0  # Number of questions the user has answered correctly
    )


# ############################################ Course ENDS HERE ####################################################


class DashStats(BaseModel_):
    numeric_stats: Dict[str, Any]
    details: Dict[str, Any]


class CourseStats(BaseModel):
    course_id: int
    title: str
    completion: Union[int, float]  # percentage of completion
    category: str


class DashStats(BaseModel):
    completed_courses_count: int
    active_courses_count: int
    pending_courses_count: int
    weekly_learning_activity: Dict[str, int]  # Days of the week as keys
    my_progress: float
    active_courses: List[CourseStats]
    certificates_count: int


class DashStatsNew(BaseModel_):
    completed_course_count: int
    active_course_count: int
    pending_course_count: int
    monthly_learning_activity: Dict[str, int]  # Months as keys
    last_monthly_learning_activity: Dict[str, int]
    my_progress: float
    total_learning_hours: float
    total_tech_learning_hours: float
    total_non_tech_learning_hours: float
    complience_total_tech_learning_target: float = 50
    complience_total_non_tech_learning_target: float = 15
    active_courses: List[CourseStats]
    certificates_count: int


class InstructorDashStatsNew(DashStatsNew):
    total_users_count: int = 0
    total_courses_count: int = 0
    approval_pending_courses_count: int = 0
    approved_courses_count: int = 0


class AdminDashStatsNew(InstructorDashStatsNew):
    total_learning_path_count: int = 0
    approval_pending_external_courses_count: int = 0


# ############################################ STATS ENDS HERE ####################################################


# Admin specific views
class AdminCourseViewFull(CourseFullDisplay):
    # Includes everything from CourseFullDisplay and additional admin-specific fields
    created_by: UserDisplay  # Display the creator of the course
    entity: str = "PIERAG"  # Entity information to which the course belongs

    class Config:
        from_attributes = True


class AdminUserView(UserDisplay):
    # Detailed view for admin to manage user details
    compliance_hours: int
    entity: str = "PIERAG"
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
        "PIERAG", description="The entity associated with the learning path"
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


class LearningPathEnrollmentRequest(BaseModel_):
    user_ids: List[int] = []


class AssignLearningPath(BaseModel_):
    learning_path_id: int
    user_ids: List[int]
    due_date: datetime

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
    user_ids: list[int]  # List of user IDs to enroll

    class Config:
        from_attributes = True


class Token(BaseModel_):
    access_token: str
    token_type: str
    user_details: Union[UserDisplay, InstructorDisplay]
    app_status: bool


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
    entities: list[str] = ["PIERAG", "All", "BTPIE"]

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
    uploaded_by: UserSortDisplay

    class Config:
        from_attributes = True


class CertificateDisplay(BaseModel_):
    id: Optional[Union[int, str]]
    issue_date: Optional[datetime]
    user: UserSortDisplay
    course: CourseSortDisplay


class QuestionSubmission(BaseModel_):
    question_id: int
    selected_option: str
    user_id: int
    source: str
    user_id: int
    course_id: int


class QuizCompletionResponse(BaseModel_):
    id: int
    question_id: int
    correct_answer: bool
    source: str
    enrollment_id: int
    attempt_no: int
    attempt_datetime: datetime


class StatusUpdate(BaseModel_):
    status_update: bool


class EmailNotification(BaseModel_):
    from_name: str
    to_email: str
    subject: str
    body: str
