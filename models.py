from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Table,
    DateTime,
    Numeric,
    Index,
)
from sqlalchemy import select, func
from sqlalchemy.orm import column_property, backref
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Association table for many-to-many relationships between users and courses
association_table = Table(
    "user_courses",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
)

# Secondary tables for many-to-many relationships
user_learning_paths = Table(
    "user_learning_paths",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("learning_path_id", ForeignKey("learning_paths.id"), primary_key=True),
)

learning_path_courses = Table(
    "learning_path_courses",
    Base.metadata,
    Column("learning_path_id", ForeignKey("learning_paths.id"), primary_key=True),
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
)


# ======================================================================


class ServiceLine(Base):
    __tablename__ = "service_line"

    name = Column(String, primary_key=True)
    # Relationships
    courses = relationship("Course", back_populates="service_line")
    admins = relationship("User", back_populates="service_line")


class Designations(Base):
    __tablename__ = "designations"
    name = Column(String, primary_key=True)


class ExternalRoles(Base):
    __tablename__ = "external_roles"

    name = Column(String, primary_key=True)


class Role(Base):
    __tablename__ = "roles"
    RoleName = Column(String, primary_key=True)
    Description = Column(String)
    # Relationships
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_creation_date = Column(DateTime, default=func.now())
    dp_file_id = Column(String, ForeignKey("files.FileID"))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    designation = Column(String, ForeignKey("designations.name"))
    role_name = Column(String, ForeignKey("roles.RoleName"))
    service_line_id = Column(Integer, ForeignKey("service_line.name"))
    total_training_hours = Column(Integer, default=0)
    counselor_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # References another user as a counselor
    entity = Column(String)  # Added to manage multi-tenancy and service line filtering
    external_role_name = Column(String, ForeignKey("external_roles.name"))
    # Relationships

    role = relationship("Role", back_populates="users")
    service_line = relationship("ServiceLine", back_populates="admins")
    courses_assigned = relationship(
        "Course", secondary=association_table, back_populates="users_assigned"
    )
    enrollments = relationship("Enrollment", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    learning_paths = relationship(
        "LearningPath", secondary=user_learning_paths, back_populates="users"
    )
    counselor = relationship('User', remote_side=[id], backref=backref('counselees', overlaps="team_members"))
    team_members = relationship('User', foreign_keys=[counselor_id], back_populates='counselor', overlaps="counselees")


    __table_args__ = (Index("idx_user_email", "email"),)


class File(Base):
    __tablename__ = "files"
    FileID = Column(String, primary_key=True)
    FileName = Column(String, nullable=False)
    FilePath = Column(String, nullable=False)
    FileType = Column(String, nullable=False)  # pdf , mp4, pptx ...
    type = Column(String, nullable=False)  # Course content, DP, thumbnail


class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    # Relationships
    course = relationship("Course", back_populates="chapters")
    contents = relationship("Content", back_populates="chapter")
    questions = relationship("Questions", back_populates="chapter")


class Questions(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    added_by = Column(Integer, ForeignKey("users.id"))
    question = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="questions")
    chapter = relationship("Chapter", back_populates="questions")

class Content(Base):
    __tablename__ = "contents"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    title = Column(String, nullable=False)
    content_type = Column(String)  # e.g., "video", "quiz", "text"
    file_id = Column(String, ForeignKey("files.FileID"))  # Link to the associated file
    # Relationships
    chapter = relationship("Chapter", back_populates="contents")
    file = relationship("File")  # Direct relationship to the File table


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enroll_date = Column(Date, default=func.now())
    year = Column(Integer)  # The year of enrollment, can be set based on enroll_date
    due_date = Column(Date)
    status = Column(String, default="Enrolled")
    completion_percentage = Column(
        Numeric, default=0
    )  # Represents overall course completion percentage
    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    progress = relationship("Progress", uselist=False, back_populates="enrollment")


class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"))
    last_chapter_id = Column(Integer, ForeignKey("chapters.id"))
    last_content_id = Column(Integer, ForeignKey("contents.id"))
    last_accessed = Column(DateTime, default=func.now())
    # Relationships
    enrollment = relationship("Enrollment", back_populates="progress")
    last_chapter = relationship("Chapter")
    last_content = relationship("Content")


class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    issue_date = Column(Date, default=func.now())
    certificate_url = Column(String)
    # Relationships
    user = relationship("User", backref="certificates")
    course = relationship("Course", backref="certificates")


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    expiry_date = Column(Date)
    # Relationships
    users = relationship(
        "User", secondary=user_learning_paths, back_populates="learning_paths"
    )
    courses = relationship(
        "Course", secondary=learning_path_courses, back_populates="learning_paths"
    )


class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    description = Column(String)
    rating = Column(Integer)
    # Relationships
    user = relationship("User", back_populates="feedbacks")
    course = relationship("Course", backref="feedbacks")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    service_line_id = Column(Integer, ForeignKey("service_line.name"))
    expected_time_to_complete = Column(Integer)
    difficulty_level = Column(
        String, default="0"
    )  # Added to store difficulty level of the course
    tags = Column(
        String, default="none"
    )  # Added to facilitate better categorization and filtering
    ratings = Column(Integer, default=0)
    status = Column(String, default="approval pending")
    creation_date = Column(
        DateTime, default=func.now()
    )  # To track when a course was created
    approved_date = Column(DateTime, default=None)  # To track when a course was created
    approved_by = Column(Integer, ForeignKey("users.id"))
    questions = relationship("Questions", back_populates="course")
    entity = Column(String)  # Added to manage multi-tenancy and service line filtering

    thumbnail_file_id = Column(String, ForeignKey("files.FileID"))

    # Relationships
    approver = relationship(
        "User", foreign_keys=[approved_by], backref="approved_courses"
    )

    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_courses"
    )
    service_line = relationship("ServiceLine", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course")
    questions = relationship("Questions", back_populates="course")  # Corrected relationship

    users_assigned = relationship(
        "User", secondary=association_table, back_populates="courses_assigned"
    )
    enrollments = relationship("Enrollment", back_populates="course")
    learning_paths = relationship(
        "LearningPath", secondary=learning_path_courses, back_populates="courses"
    )


    # Calculated fields

    chapters_count = column_property(
        select(func.count(Chapter.id))
        .where(Chapter.course_id == id)
        .scalar_subquery()
    )

    enrolled_students_count = column_property(
        select(func.count(Enrollment.id))
        .where(Enrollment.course_id == id)
        .scalar_subquery()
    )
    feedback_count = column_property(
        select(func.count(Feedback.id))
        .where(Feedback.course_id == id)
        .scalar_subquery()
    )
    completed_students_count = column_property(
        select(func.count(Enrollment.id))
        .where((Enrollment.course_id == id) & (Enrollment.status == "Completed"))
        .scalar_subquery()
    )
    average_rating = column_property(
        select(func.avg(Feedback.rating))
        .where(Feedback.course_id == id)
        .scalar_subquery()
    )