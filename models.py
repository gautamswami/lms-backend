from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    UserID = Column(Integer, primary_key=True, autoincrement=True)
    UserName = Column(String, nullable=False)
    Password = Column(String, nullable=False)
    Email = Column(String, unique=True, nullable=False)
    Role = Column(String, nullable=False)  # Admin, Trainer, User
    Credits = Column(Integer, default=0)

    # Relationships
    enrollments = relationship('Enrollment', back_populates='user')
    assessment_results = relationship('AssessmentResult', back_populates='user')
    # reports = relationship('Report', back_populates='admin')
    created_courses = relationship('Course', back_populates='creator')


class Course(Base):
    __tablename__ = 'courses'

    CourseID = Column(Integer, primary_key=True, autoincrement=True)
    CourseName = Column(String, nullable=False)
    Description = Column(String)
    Category = Column(String)
    Difficulty = Column(String)
    MostPopular = Column(Boolean, default=False)
    Mandatory = Column(Boolean, default=False)
    ExpectedTimeToComplete = Column(Integer)
    Credits = Column(Integer, default=0)
    CreatedBy = Column(Integer, ForeignKey('users.UserID'), nullable=False)

    # Relationships
    contents = relationship('CourseContent', back_populates='course')
    quizzes = relationship('Quiz', back_populates='course')
    assessments = relationship('Assessment', back_populates='course')
    enrollments = relationship('Enrollment', back_populates='course')
    creator = relationship('User', back_populates='created_courses')


class CourseContent(Base):
    __tablename__ = 'course_contents'

    ContentID = Column(Integer, primary_key=True, autoincrement=True)
    CourseID = Column(Integer, ForeignKey('courses.CourseID'), nullable=False)
    ContentType = Column(String)  # PPTX, Video, PDF, Word, MP3
    ContentURL = Column(String, nullable=False)
    Order = Column(Integer, nullable=False)

    # Relationships
    course = relationship('Course', back_populates='contents')


class Quiz(Base):
    __tablename__ = 'quizzes'

    QuizID = Column(Integer, primary_key=True, autoincrement=True)
    CourseID = Column(Integer, ForeignKey('courses.CourseID'), nullable=False)
    Question = Column(String, nullable=False)
    Options = Column(String, nullable=False)  # JSON or delimited string
    CorrectAnswer = Column(String, nullable=False)

    # Relationships
    course = relationship('Course', back_populates='quizzes')


class Enrollment(Base):
    __tablename__ = 'enrollments'

    EnrollmentID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CourseID = Column(Integer, ForeignKey('courses.CourseID'), nullable=False)
    EnrollDate = Column(Date, nullable=False)
    EndDate = Column(Date, nullable=False)
    Status = Column(String, nullable=False)  # Pending, Completed, Failed
    TimeSpent = Column(Integer, default=0)

    # Relationships
    user = relationship('User', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')


class Assessment(Base):
    __tablename__ = 'assessments'

    AssessmentID = Column(Integer, primary_key=True, autoincrement=True)
    CourseID = Column(Integer, ForeignKey('courses.CourseID'), nullable=False)
    AssessmentType = Column(String, nullable=False)  # MCQ
    PassMark = Column(Integer, nullable=False)

    # Relationships
    course = relationship('Course', back_populates='assessments')
    assessment_results = relationship('AssessmentResult', back_populates='assessment')


class AssessmentResult(Base):
    __tablename__ = 'assessment_results'

    ResultID = Column(Integer, primary_key=True, autoincrement=True)
    AssessmentID = Column(Integer, ForeignKey('assessments.AssessmentID'), nullable=False)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    Score = Column(Integer, nullable=False)
    Status = Column(String, nullable=False)  # Pass, Fail
    CertificateGenerated = Column(Boolean, default=False)
    Badge = Column(Boolean, default=False)

    # Relationships
    assessment = relationship('Assessment', back_populates='assessment_results')
    user = relationship('User', back_populates='assessment_results')


class FileMetadata(Base):
    __tablename__ = 'file_metadata'

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    path = Column(String, nullable=True)


# class Report(Base):
#     __tablename__ = 'reports'
#
#     ReportID = Column(Integer, primary_key=True, autoincrement=True)
#     AdminID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
#     UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
#     CourseID = Column(Integer, ForeignKey('courses.CourseID'), nullable=False)
#     SuccessRate = Column(Float, nullable=False)
#
#     # Relationships
#     admin = relationship('User', foreign_keys=[AdminID], back_populates='reports')
#     user = relationship('User', foreign_keys=[UserID])
#     course = relationship('Course')

if __name__ == '__main__':
    # Database connection
    engine = create_engine('sqlite:///lms.db')
    Base.metadata.create_all(engine)

    # Session setup
    Session = sessionmaker(bind=engine)
    session = Session()

    # Example usage:
    new_user = User(UserName='John Doe', Password='secure-password', Email='johndoe@example.com', Role='Admin')
    session.add(new_user)
    session.commit()
