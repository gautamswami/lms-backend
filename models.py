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
    extract,
    Boolean,
    case,
    cast,
    Float,
    Join,
    UniqueConstraint,
)
from sqlalchemy import select, func
from sqlalchemy.orm import column_property, backref
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import and_
from database import SessionLocal
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

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


class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    rating = Column(Integer)
    # Relationships
    user = relationship("User", back_populates="feedbacks", foreign_keys=[user_id])
    course = relationship("Course", backref="feedbacks")
    submitter = relationship(
        "User", foreign_keys=[submitted_by], back_populates="feedback_given"
    )


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
    service_line_id = Column(String, ForeignKey("service_line.name"))
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
    feedbacks = relationship(
        "Feedback", back_populates="user", foreign_keys=[Feedback.user_id]
    )
    feedback_given = relationship(
        "Feedback", back_populates="submitter", foreign_keys=[Feedback.submitted_by]
    )
    counselor = relationship(
        "User", remote_side=[id], backref=backref("counselees", overlaps="team_members")
    )
    team_members = relationship(
        "User",
        foreign_keys=[counselor_id],
        back_populates="counselor",
        overlaps="counselees",
    )
    external_certifications = relationship(
        "ExternalCertification",
        foreign_keys="[ExternalCertification.uploaded_by_id]",
        back_populates="uploaded_by",
        cascade="all, delete-orphan",
    )
    approved_certifications = relationship(
        "ExternalCertification",
        foreign_keys="[ExternalCertification.approved_by]",
        back_populates="approver",
        cascade="all, delete-orphan",
    )
    learning_path_enrollments = relationship(
        "LearningPathEnrollment", back_populates="user"
    )  # This line is added
    # Ensuring the relationship is explicitly stated (if needed for clarity or other ORM reasons)
    certificates = relationship("Certificate", back_populates="user")

    @property
    def certificates_count(self):
        return len(self.certificates)

    # Properties for total learning hours, tech, and non-tech learning hours
    @property
    def total_learning_hours(self):
        return self.get_total_learning_hours(self.id)

    @property
    def total_tech_learning_hours(self):
        return self.get_total_tech_learning_hours(self.id)

    @property
    def total_non_tech_learning_hours(self):
        return self.get_total_non_tech_learning_hours(self.id)

    @staticmethod
    def get_total_learning_hours(user_id):
        session = SessionLocal()

        # Query 1: Sum of completed_hours from Enrollment
        completed_hours_query = session.query(
            func.coalesce(func.sum(Enrollment.completed_hours), 0)
        ).filter(Enrollment.user_id == user_id).scalar()

        # Query 2: Sum of hours from ExternalCertification (only approved ones)
        certification_hours_query = session.query(
            func.coalesce(func.sum(ExternalCertification.hours), 0)
        ).filter(
            ExternalCertification.uploaded_by_id == user_id,
            ExternalCertification.status == 'approved'
        ).scalar()

        # Combine the results
        total_learning_hours = completed_hours_query + certification_hours_query

        session.close()  # Make sure to close the session
        return total_learning_hours

    @staticmethod
    def get_total_tech_learning_hours(user_id):
        session = SessionLocal()

        # Query 1: Sum of completed_hours for technical courses from Enrollment
        tech_completed_hours_query = session.query(
            func.coalesce(func.sum(Enrollment.completed_hours), 0)
        ).join(Course).filter(
            Enrollment.user_id == user_id,
            Course.category == 'technical'
        ).scalar()

        # Query 2: Sum of hours from ExternalCertification (technical, approved ones)
        tech_certification_hours_query = session.query(
            func.coalesce(func.sum(ExternalCertification.hours), 0)
        ).filter(
            ExternalCertification.uploaded_by_id == user_id,
            ExternalCertification.category == 'technical',
            ExternalCertification.status.in_(['approve', 'approved'])
        ).scalar()

        # Combine the results
        total_tech_learning_hours = tech_completed_hours_query + tech_certification_hours_query

        session.close()  # Make sure to close the session
        return total_tech_learning_hours

    @staticmethod
    def get_total_non_tech_learning_hours(user_id):
        session = SessionLocal()

        # Query 1: Sum of completed_hours for non-technical courses from Enrollment
        non_tech_completed_hours_query = session.query(
            func.coalesce(func.sum(Enrollment.completed_hours), 0)
        ).join(Course).filter(
            Enrollment.user_id == user_id,
            Course.category == 'nonTechnical'
        ).scalar()

        print(non_tech_completed_hours_query,'non_tech_completed_hours_query')

        # Query 2: Sum of hours from ExternalCertification (non-technical, approved ones)
        non_tech_certification_hours_query = session.query(
            func.coalesce(func.sum(ExternalCertification.hours), 0)
        ).filter(
            ExternalCertification.uploaded_by_id == user_id,
            ExternalCertification.category == 'nonTechnical',
            ExternalCertification.status.in_(['approve', 'approved'])
        ).scalar()
        print(non_tech_certification_hours_query,'non_tech_certification_hours_query')
        # Combine the results
        total_non_tech_learning_hours = non_tech_completed_hours_query + non_tech_certification_hours_query

        session.close()  # Make sure to close the session
        return total_non_tech_learning_hours

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
    expected_time_to_complete = Column(Integer, default=5)

    # Relationships
    chapter = relationship("Chapter", back_populates="contents")
    file = relationship("File")  # Direct relationship to the File table


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enroll_date = Column(Date, default=func.now())
    year = Column(
        Integer, default=lambda: extract("year", func.now())
    )  # Default value of current year
    due_date = Column(Date, nullable=True)
    status = Column(String, default="Enrolled")
    # completion_percentage = Column(
    #     Numeric, default=0
    # )  # Represents overall course completion percentage
    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    progress = relationship("Progress", uselist=False, back_populates="enrollment")

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="_user_course_uc"),)

    @property
    def calculated_completion_percentage(self):
        session = SessionLocal()  # Assuming Session is imported and configured properly
        return self.calculate_progress_percentage_(self.id, session)

    @staticmethod
    def calculate_progress_percentage_(enrollment_id, session):
        """
        Calculates the progress percentage for a given enrollment based on the number of contents completed.
        Handles cases where there might be no content, chapters, or progress records.

        Args:
        enrollment_id (int): The ID of the enrollment.
        session (Session): The SQLAlchemy session for database interaction.

        Returns:
        float: The progress percentage of the enrollment, or 0.0 if insufficient data exists.
        """
        # Retrieve the enrollment and associated course details
        enrollment = session.query(Enrollment).filter_by(id=enrollment_id).one_or_none()
        if not enrollment:
            # print("Enrollment not found.")
            return 0.0  # Handle case where enrollment doesn't exist

        course_id = enrollment.course_id
        print("course_id", course_id)

        # Check for the existence of chapters before counting content
        chapters_exist = session.query(Chapter).filter_by(course_id=course_id).first()
        if not chapters_exist:
            # print("No chapters available for this course.")
            return 0.0  # Return 0% if no chapters are available

        # Get the total number of contents in the course
        total_contents = (
            session.query(func.count(Content.id))
            .join(Chapter)
            .filter(Chapter.course_id == course_id)
            .scalar()
        )
        print("total_contents", total_contents)

        if total_contents == 0:
            # print("No contents available in the course.")
            return 0.0  # Return 0% if no contents are available

        # Check if there's any progress recorded
        if not enrollment.progress or not enrollment.progress.content_id:
            # print("No progress recorded for this enrollment.")
            return 0.0  # Return 0% if no progress is found

        # Count the number of contents completed
        content_id = enrollment.progress.content_id
        last_content = session.query(Content).filter_by(id=content_id).one_or_none()
        if not last_content:
            # print("Last content not found.")
            return 0.0  # Handle case where last content doesn't exist

        chapter_id = last_content.chapter_id
        # print("chapter_id", chapter_id)

        completed_contents = (
            session.query(func.count(Content.id))
            .join(Chapter)
            .filter(
                and_(
                    Chapter.course_id == course_id,
                    Content.id <= content_id,
                    Chapter.id <= chapter_id,
                )
            )
            .scalar()
        )
        # print("completed_contents", completed_contents)

        # Calculate progress percentage
        progress_percentage = (completed_contents / total_contents) * 100
        # print("progress_percentage", progress_percentage)
        return progress_percentage


class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    content_id = Column(Integer, ForeignKey("contents.id"))
    completed_at = Column(DateTime, default=func.now())
    # Relationships
    enrollment = relationship("Enrollment", back_populates="progress")
    last_chapter = relationship("Chapter")
    last_content = relationship("Content")

    __table_args__ = (
        UniqueConstraint("enrollment_id", "content_id", name="_enrollment_content_uc"),
    )


class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    issue_date = Column(DateTime, default=func.now())
    # certificate_url = Column(String)
    # Relationships
    user = relationship("User", back_populates="certificates")
    course = relationship("Course", backref="certificates")

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="_user_course_uc"),)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    service_line_id = Column(String, ForeignKey("service_line.name"))
    entity = Column(String)

    courses = relationship(
        "Course", secondary=learning_path_courses, back_populates="learning_paths"
    )
    enrollments = relationship("LearningPathEnrollment", back_populates="learning_path")

    @property
    def expected_time_to_complete(self):
        return sum(course.expected_time_to_complete for course in self.courses)


class LearningPathEnrollment(Base):
    __tablename__ = "learning_path_enrollments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
    enroll_date = Column(Date, default=func.now())
    year = Column(
        Integer, default=lambda: extract("year", func.now())
    )  # Default value of current year
    due_date = Column(Date, nullable=True, default=func.now())
    status = Column(String, default="Enrolled")
    completion_percentage = Column(
        Numeric, default=0
    )  # Represents overall course completion percentage

    # Relationships

    # Relationships
    user = relationship("User", back_populates="learning_path_enrollments")
    learning_path = relationship("LearningPath", back_populates="enrollments")

    @property
    def calculate_progress_percentage(self):
        total_contents = 0
        completed_contents = 0

        for course in self.learning_path.courses:
            total_contents += sum(len(chapter.contents) for chapter in course.chapters)
            for chapter in course.chapters:
                for content in chapter.contents:
                    if content.id <= self.progress.content_id:
                        completed_contents += 1

        if total_contents == 0:
            return 0
        return (completed_contents / total_contents) * 100

    __table_args__ = (
        UniqueConstraint("user_id", "learning_path_id", name="_user_learning_path_uc"),
    )


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    service_line_id = Column(String, ForeignKey("service_line.name"))
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
    approved_date = Column(
        DateTime, default=None
    )  # To track when a course was approved
    approved_by = Column(Integer, ForeignKey("users.id"))
    entity = Column(String)  # Added to manage multi-tenancy and service line filtering
    thumbnail_file_id = Column(String, ForeignKey("files.FileID"))

    # Relationships
    approver = relationship(
        "User", foreign_keys=[approved_by], backref="approved_courses"
    )
    creator = relationship("User", foreign_keys=[created_by], backref="created_courses")
    service_line = relationship("ServiceLine", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course")
    questions = relationship(
        "Questions", back_populates="course"
    )  # Corrected relationship
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
        .correlate_except(Chapter)
        .scalar_subquery()
    )

    enrolled_students_count = column_property(
        select(func.count(Enrollment.id))
        .where(Enrollment.course_id == id)
        .correlate_except(Enrollment)
        .scalar_subquery()
    )

    completed_students_count = column_property(
        select(func.count(Enrollment.id))
        .where((Enrollment.course_id == id) & (Enrollment.status == "Completed"))
        .correlate_except(Enrollment)
        .scalar_subquery()
    )

    average_rating = column_property(
        select(func.avg(Feedback.rating))
        .where(Feedback.course_id == id)
        .correlate_except(Feedback)
        .scalar_subquery()
    )

    feedback_count = column_property(
        select(func.count(Feedback.rating))
        .where(Feedback.course_id == id)
        .correlate_except(Feedback)
        .scalar_subquery()
    )


class ExternalCertification(Base):
    __tablename__ = "external_certifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, default="pending")
    date_of_completion = Column(Date, nullable=False)
    hours = Column(Integer, nullable=False)
    file_id = Column(String, ForeignKey("files.FileID"), nullable=False)
    certificate_provider = Column(String, nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_date = Column(
        DateTime, default=None
    )  # To track when a course was approved
    approved_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    file = relationship("File")
    uploaded_by = relationship(
        "User", foreign_keys=[uploaded_by_id], back_populates="external_certifications"
    )
    approver = relationship(
        "User", foreign_keys=[approved_by], back_populates="approved_certifications"
    )

    @property
    def sample_property(self):
        return len(self.uploaded_by.uploaded_certifications)


class QuizCompletions(Base):
    __tablename__ = "quiz_completions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    correct_answer = Column(Boolean, nullable=False)
    source = Column(String, nullable=False)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    attempt_datetime = Column(DateTime, default=datetime.now)

    def calculate_attempt_no(self, db):
        """Calculate the attempt number before inserting a new record."""
        return (
                db.query(func.count(QuizCompletions.id))
                .filter(
                    QuizCompletions.question_id == self.question_id,
                    QuizCompletions.enrollment_id == self.enrollment_id,
                )
                .scalar()
                + 1
        )


class AppStatus(Base):
    __tablename__ = "app_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    status_update = Column(Boolean, nullable=False)
    update_datetime = Column(DateTime, default=datetime.now)


Chapter.expected_time_to_complete = column_property(
    select(func.coalesce(func.sum(Content.expected_time_to_complete), 0))
    .where(Content.chapter_id == Chapter.id)
    .correlate_except(Content)
    .label("expected_time_to_complete")
)

Course.expected_time_to_complete = column_property(
    select(func.coalesce(func.sum(Chapter.expected_time_to_complete), 0))
    .where(Chapter.course_id == Course.id)
    .correlate_except(Chapter)
    .label("expected_time_to_complete")
)
Enrollment.expected_time_to_complete = column_property(
    select(func.coalesce(Course.expected_time_to_complete, 0))
    .where(Course.id == Enrollment.course_id)
    .correlate_except(Course)
    .label("expected_time_to_complete")
)

Enrollment.completed_hours = column_property(
    select(func.coalesce(func.sum(Content.expected_time_to_complete), 0))
    .where(
        Progress.enrollment_id == Enrollment.id, Content.id == Progress.content_id
    )  # Ensuring it's for the current enrollment
    .correlate_except(Content, Progress)
    .label("completed_hours")
)

# Calculate the completion percentage
Enrollment.completion_percentage = column_property(
    select(
        cast(
            100
            * func.coalesce(Enrollment.completed_hours, 0)
            / func.coalesce(Enrollment.expected_time_to_complete, 0),
            Float,
        )
    )
    .correlate_except(Course)
    .label("completion_percentage")
)
Enrollment.pending_question_count = column_property(
    select(func.count(Questions.id))
    .select_from(Questions)
    .join(Course)
    .outerjoin(
        QuizCompletions,
        and_(
            QuizCompletions.question_id == Questions.id,
            QuizCompletions.enrollment_id == Enrollment.id,
            QuizCompletions.correct_answer == True,
        ),
    )
    .filter(
        Course.id == Enrollment.course_id,
        QuizCompletions.id.is_(None),  # No completion record for this question
    )
    .correlate_except(QuizCompletions)
    .scalar_subquery()
)

Enrollment.status = column_property(
    case(
        (and_(Enrollment.completed_hours > 0,
              Enrollment.completed_hours < Enrollment.expected_time_to_complete), "Active"),
        (and_(Enrollment.completed_hours == Enrollment.expected_time_to_complete,
              Enrollment.pending_question_count == 0), "Completed"),
        else_="Pending"
    ).label("status")
)
Enrollment.pending_chapter_count = column_property(
    select(func.count(Chapter.id))
    .select_from(Chapter)
    .join(Content)
    .outerjoin(
        Progress,
        and_(
            Progress.content_id == Content.id,
            Progress.enrollment_id == Enrollment.id,
        ),
    )
    .filter(
        Chapter.course_id == Enrollment.course_id,
        Progress.completed_at.is_(None),
    )
    .correlate_except(Progress)
    .scalar_subquery()
)

#
# ServiceLine.total_courses = column_property(
#     select(func.count(Course.id))
#     .where(Course.service_line_id == ServiceLine.name)
#     .correlate_except(Course)
#     .label("total_courses")
# )

# User.total_learning_hours = column_property(
#     select(func.coalesce(func.sum(Enrollment.completed_hours), 0))
#     .where(Enrollment.user_id == User.id)  # Filter Enrollments by User's ID
#     .label("total_learning_hours")
# )
# User.total_tech_learning_hours = column_property(
#     select(func.coalesce(func.sum(Enrollment.completed_hours), 0))
#     .select_from(User)  # Start explicitly from User
#     .join(Enrollment, User.id == Enrollment.user_id)  # Join User to Enrollment
#     .join(Course, Enrollment.course_id == Course.id)  # Join Enrollment to Course
#     .where(
#         (Enrollment.user_id == User.id) & (Course.category == "technical")
#     )  # Apply filters
#     .label("total_tech_learning_hours")
# )

# User.total_non_tech_learning_hours = column_property(
#     select(func.coalesce(func.sum(Enrollment.completed_hours), 0))
#     .select_from(User)  # Start explicitly from User
#     .join(Enrollment, User.id == Enrollment.user_id)  # Join User to Enrollment
#     .join(Course, Enrollment.course_id == Course.id)  # Join Enrollment to Course
#     .where(
#         (Enrollment.user_id == User.id) & (Course.category == "nonTechnical")
#     )  # Apply filters
#     .label("total_non_tech_learning_hours")
# )


# User.total_learning_hours = column_property(
#     select(
#         func.coalesce(func.sum(Enrollment.completed_hours), 0) +
#         func.coalesce(func.sum(ExternalCertification.hours), 0)
#     )
#     .outerjoin(ExternalCertification, ExternalCertification.uploaded_by_id == User.id)
#     .where(
#         (ExternalCertification.status == "approved") | (Enrollment.user_id == User.id)
#     )
#     .label("total_learning_hours")
# )
# User.total_tech_learning_hours = column_property(
#     select(
#         func.coalesce(func.sum(Enrollment.completed_hours), 0) +
#         func.coalesce(func.sum(ExternalCertification.hours), 0)
#     )
#     .select_from(User)
#     .outerjoin(Enrollment, User.id == Enrollment.user_id)
#     .outerjoin(Course, Enrollment.course_id == Course.id)
#     .outerjoin(ExternalCertification, ExternalCertification.uploaded_by_id == User.id)
#     .where(
#         (Course.category == "technical") |
#         (ExternalCertification.category == "technical") &
#         (ExternalCertification.status == "approved")
#     )
#     .label("total_tech_learning_hours")
# )

# User.total_non_tech_learning_hours = column_property(
#     select(
#         func.coalesce(func.sum(Enrollment.completed_hours), 0) +
#         func.coalesce(func.sum(ExternalCertification.hours), 0)
#     )
#     .select_from(User)
#     .outerjoin(Enrollment, User.id == Enrollment.user_id)
#     .outerjoin(Course, Enrollment.course_id == Course.id)
#     .outerjoin(ExternalCertification, ExternalCertification.uploaded_by_id == User.id)
#     .where(
#         (Course.category == "nonTechnical") |
#         (ExternalCertification.category == "nonTechnical") &
#         (ExternalCertification.status == "approved")
#     )
#     .label("total_non_tech_learning_hours")
# )

User.completion_percentage = column_property(
    select(cast(func.coalesce(func.avg(Enrollment.completion_percentage), 0), Float))
    .where(Enrollment.user_id == User.id)
    .correlate_except(Enrollment)
    .label("user_completion_percentage")
)

User.total_tech_enrolled_hours = column_property(
    select(func.coalesce(func.sum(Course.expected_time_to_complete), 0))
    .select_from(Enrollment)
    .join(Course, Enrollment.course_id == Course.id)
    .where((Enrollment.user_id == User.id) & (Course.category == "technical"))
    .correlate_except(Course)
    .label("total_tech_enrolled_hours")
)

User.total_non_tech_enrolled_hours = column_property(
    select(func.coalesce(func.sum(Course.expected_time_to_complete), 0))
    .select_from(Enrollment)
    .join(Course, Enrollment.course_id == Course.id)
    .where((Enrollment.user_id == User.id) & (Course.category == "nonTechnical"))
    .correlate_except(Course)
    .label("total_non_tech_enrolled_hours")
)
