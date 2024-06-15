from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, Table, DateTime, Numeric
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for many-to-many relationships between users and courses
association_table = Table('user_courses', Base.metadata,
                          Column('user_id', ForeignKey('users.id'), primary_key=True),
                          Column('course_id', ForeignKey('courses.id'), primary_key=True))


class ServiceLine(Base):
    __tablename__ = 'service_line'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # Relationships
    courses = relationship('Course', back_populates='service_line')
    admins = relationship('User', back_populates='service_line')


class Role(Base):
    __tablename__ = 'roles'
    RoleName = Column(String, primary_key=True)
    Description = Column(String)
    # Relationships
    users = relationship('User', back_populates='role')


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_creation_date = Column(DateTime, default=func.now())
    dp_file_id = Column(String, ForeignKey('files.FileID'))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    designation = Column(String)
    role_name = Column(String, ForeignKey('roles.RoleName'))
    service_line_id = Column(Integer, ForeignKey('service_line.id'))
    total_training_hours = Column(Integer, default=0)

    # Relationships
    role = relationship('Role', back_populates='users')
    service_line = relationship('ServiceLine', back_populates='admins')
    courses_assigned = relationship('Course', secondary=association_table, back_populates='users_assigned')
    enrollments = relationship('Enrollment', back_populates='user')
    feedbacks = relationship('Feedback', back_populates='user')
    learning_paths = relationship('LearningPath', secondary='user_learning_paths', back_populates='users')


class File(Base):
    __tablename__ = 'files'
    FileID = Column(String, primary_key=True)
    FileName = Column(String, nullable=False)
    FilePath = Column(String, nullable=False)
    FileType = Column(String, nullable=False)  # pdf , mp4, pptx ...
    type = Column(String, nullable=False)  # Course content, DP, thumbnail


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    created_by = Column(Integer, ForeignKey('users.id'))
    service_line_id = Column(Integer, ForeignKey('service_line.id'))
    expected_time_to_complete = Column(Integer)
    ratings = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    creation_date = Column(DateTime, default=func.now())  # To track when a course was created
    approved_date = Column(DateTime, default=func.now())  # To track when a course was created
    approved_by = Column(Integer, ForeignKey('users.id'))

    thumbnail_file_id = Column(String, ForeignKey('files.FileID'))

    # Relationships
    service_line = relationship('ServiceLine', back_populates='courses')
    chapters = relationship('Chapter', back_populates='course')
    users_assigned = relationship('User', secondary=association_table, back_populates='courses_assigned')
    enrollments = relationship('Enrollment', back_populates='course')


class Chapter(Base):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    title = Column(String, nullable=False)
    # Relationships
    course = relationship('Course', back_populates='chapters')
    contents = relationship('Content', back_populates='chapter')


class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    title = Column(String, nullable=False)
    content_type = Column(String)  # e.g., "video", "quiz", "text"
    file_id = Column(String, ForeignKey('files.FileID'))  # Link to the associated file
    # Relationships
    chapter = relationship('Chapter', back_populates='contents')
    file = relationship('File')  # Direct relationship to the File table


class Enrollment(Base):
    __tablename__ = 'enrollments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    enroll_date = Column(Date, default=func.now())
    year = Column(Integer)  # The year of enrollment, can be set based on enroll_date
    due_date = Column(Date)
    status = Column(String, default="Enrolled")
    completion_percentage = Column(Numeric)  # Represents overall course completion percentage
    # Relationships
    user = relationship('User', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')
    progress = relationship('Progress', uselist=False, back_populates='enrollment')


class Progress(Base):
    __tablename__ = 'progress'
    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey('enrollments.id'))
    last_chapter_id = Column(Integer, ForeignKey('chapters.id'))
    last_content_id = Column(Integer, ForeignKey('contents.id'))
    last_accessed = Column(DateTime, default=func.now())
    # Relationships
    enrollment = relationship('Enrollment', back_populates='progress')
    last_chapter = relationship('Chapter')
    last_content = relationship('Content')


class Certificate(Base):
    __tablename__ = 'certificates'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    issue_date = Column(Date, default=func.now())
    certificate_url = Column(String)
    # Relationships
    user = relationship('User', backref='certificates')
    course = relationship('Course', backref='certificates')


class LearningPath(Base):
    __tablename__ = 'learning_paths'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    expiry_date = Column(Date)
    # Relationships
    users = relationship('User', secondary='user_learning_paths', back_populates='learning_paths')
    courses = relationship('Course', secondary='learning_path_courses', back_populates='learning_paths')


class Feedback(Base):
    __tablename__ = 'feedbacks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    description = Column(String)
    rating = Column(Integer)
    # Relationships
    user = relationship('User', back_populates='feedbacks')
    course = relationship('Course', backref='feedbacks')


# Secondary tables for many-to-many relationships
user_learning_paths = Table('user_learning_paths', Base.metadata,
                            Column('user_id', ForeignKey('users.id'), primary_key=True),
                            Column('learning_path_id', ForeignKey('learning_paths.id'), primary_key=True))

learning_path_courses = Table('learning_path_courses', Base.metadata,
                              Column('learning_path_id', ForeignKey('learning_paths.id'), primary_key=True),
                              Column('course_id', ForeignKey('courses.id'), primary_key=True))


class FileMetadata:
    pass