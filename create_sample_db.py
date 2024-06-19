from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import uuid
from models import *
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = "sqlite:///./lms.db"  # Update this to your actual database URL

# Create the engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def create_sample_data():
    db = SessionLocal()
    try:

        service_lines = [
            "Business Risk",
            "Assurance",
            "Stat Audit",
            "Accounting Advisory",
            "Tech Risk",
            "HR",
            "Operations",
            "Pursuits",
            "IT Operations",
            "Content Writer",
            "Website Operation Specialist",
            "Financial Due Diligence",
            "Brands, Marketing and Communications",
        ]
        designations = [
            "Co-Founder - Assurance and Advisory Leader",
            "Director",
            "Senior Consultant",
            "Senior",
            "Manager",
            "Associate Director",
            "Assistant Manager",
            "Consultant",
            "Associate",
            "Executive - Operations",
            "Executive",
            "Executive Assistant",
            "Associate (Support) – Operations",
            "Trainee",
        ]
        external_roles = [
            "Business Risk",
            "Assurance",
            "Stat Audit",
            "Accounting Advisory",
            "Tech Risk",
            "HR",
            "Operations",
            "Pursuits",
            "IT Operations",
            "Content Writer",
            "Website Operation Specialist",
            "Financial Due Diligence",
            "Brands, Marketing and Communications",
        ]

        # Add service lines
        for name in service_lines:
            service_line = ServiceLine(name=name)
            db.add(service_line)

        # Add designations
        for name in designations:
            designation = Designations(name=name)
            db.add(designation)

        # Add external roles
        for name in external_roles:
            external_role = ExternalRoles(name=name)
            db.add(external_role)

        db.commit()

        # Create roles
        roles = [
            Role(RoleName="Super Admin", Description="Manages the whole system"),
            Role(RoleName="Admin", Description="Manages a specific LOB or department"),
            Role(
                RoleName="Instructor",
                Description="Manages own courses and can propose new ones",
            ),
            Role(RoleName="Employee", Description="Can view and enroll in courses"),
        ]
        db.add_all(roles)
        db.commit()

        # Create service lines
        service_lines = [
            ServiceLine(name="Software Development"),
            ServiceLine(name="Data Science"),
        ]
        db.add_all(service_lines)
        db.commit()

        # Create users
        super_admin = User(
            email="superadmin@example.com",
            password=pwd_context.hash("password"),
            first_name="Super",
            last_name="Admin",
            role_name="Super Admin",
            employee_id="SA001",
            designation="Manager",
            service_line_id=service_lines[0].name,
            external_role_name="Assurance",
        )
        admin = User(
            email="admin@example.com",
            password=pwd_context.hash("password"),
            first_name="Admin",
            last_name="User",
            role_name="Admin",
            employee_id="AD001",
            designation="Manager",
            service_line_id=service_lines[0].name,
            external_role_name="Pursuits",
        )
        instructor = User(
            email="instructor@example.com",
            password=pwd_context.hash("password"),
            first_name="Instructor",
            last_name="User",
            role_name="Instructor",
            employee_id="IN001",
            designation="Manager",
            service_line_id=service_lines[0].name,
            external_role_name="Pursuits",
        )

        db.add_all([super_admin, admin, instructor])
        db.commit()

        employee = User(
            email="employee@example.com",
            password=pwd_context.hash("password"),
            first_name="Employee",
            last_name="User",
            role_name="Employee",
            employee_id="EM001",
            designation="Manager",
            service_line_id=service_lines[0].name,
            counselor_id=instructor.id,
            external_role_name="Pursuits",
        )

        NONE = User(
            email="admin@abc.com",
            password=pwd_context.hash("password"),
            first_name="Employee",
            last_name="User",
            role_name="Admin",
            employee_id="EM001",
            designation="Manager",
            service_line_id=service_lines[0].name,
            counselor_id=instructor.id,
            external_role_name="Pursuits",
        )

        db.add_all([employee, NONE])
        db.commit()

        # Create courses
        course1 = Course(
            title="Intro to Python",
            description="Learn Python basics",
            category="Programming",
            created_by=admin.id,
            service_line_id=service_lines[0].name,
            expected_time_to_complete=10,
        )
        course2 = Course(
            title="Advanced Data Science",
            description="Deep dive into data science techniques",
            category="Data Science",
            created_by=instructor.id,
            service_line_id=service_lines[1].name,
            expected_time_to_complete=20,
        )

        db.add_all([course1, course2])
        db.commit()

        # Create chapters
        chapter1 = Chapter(
            course_id=course1.id,
            title="Python Basics",
            description="Introduction to Python programming",
        )
        chapter2 = Chapter(
            course_id=course1.id,
            title="Advanced Python",
            description="Advanced concepts in Python programming",
        )

        db.add_all([chapter1, chapter2])
        db.commit()

        # Create content
        content1 = Content(
            chapter_id=chapter1.id,
            title="Python Installation",
            content_type="video",
            file_id=str(uuid.uuid4()),
        )
        content2 = Content(
            chapter_id=chapter1.id,
            title="Hello World",
            content_type="video",
            file_id=str(uuid.uuid4()),
        )

        db.add_all([content1, content2])
        db.commit()

        # Create enrollments
        enrollment1 = Enrollment(
            user_id=employee.id,
            course_id=course1.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=course1.expected_time_to_complete),
            year=datetime.now().year,
        )
        enrollment2 = Enrollment(
            user_id=employee.id,
            course_id=course2.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=course2.expected_time_to_complete),
            year=datetime.now().year,
        )

        db.add_all([enrollment1, enrollment2])
        db.commit()

        # Create progress
        progress1 = Progress(
            enrollment_id=enrollment1.id,
            last_chapter_id=chapter1.id,
            last_content_id=content1.id,
            last_accessed=datetime.now(),
        )
        progress2 = Progress(
            enrollment_id=enrollment2.id,
            last_chapter_id=chapter2.id,
            last_content_id=content2.id,
            last_accessed=datetime.now(),
        )

        db.add_all([progress1, progress2])
        db.commit()

        # Create files
        file1 = File(
            FileID=str(uuid.uuid4()),
            FileName="intro_python.mp4",
            FilePath="/files/intro_python.mp4",
            FileType="video/mp4",
            type="Course content",
        )
        file2 = File(
            FileID=str(uuid.uuid4()),
            FileName="advanced_data_science.pdf",
            FilePath="/files/advanced_data_science.pdf",
            FileType="application/pdf",
            type="Course content",
        )

        db.add_all([file1, file2])
        db.commit()

        # Create feedback
        feedback1 = Feedback(
            user_id=employee.id,
            course_id=course1.id,
            description="Great course!",
            rating=5,
        )
        feedback2 = Feedback(
            user_id=employee.id,
            course_id=course2.id,
            description="Very informative.",
            rating=4,
        )

        db.add_all([feedback1, feedback2])
        db.commit()

        # Create learning paths
        learning_path1 = LearningPath(
            name="Python Developer Path",
            expiry_date=datetime.now() + timedelta(days=365),
        )
        learning_path1.courses.append(course1)
        learning_path1.users.append(employee)

        db.add(learning_path1)
        db.commit()

        print("Sample data created successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
