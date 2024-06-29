import uuid
from datetime import datetime, timedelta, date

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import *

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
            Role(RoleName="Instructor", Description="Manages own courses and can propose new ones"),
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

        db.add(employee)
        db.commit()

        # Create courses
        course1 = Course(
            title="course1",
            description="Learn Python basics",
            category="Programming",
            created_by=instructor.id,
            service_line_id=service_lines[0].name,
            expected_time_to_complete=10,
            tags="advanced,ml",
        )
        course2 = Course(
            title="The Complete Histudy 2024: From Zero to Expert!",
            description="## What you'll learn\n\nAre you new to PHP or need a refresher? Then this course will help you get all the fundamentals of Procedural PHP, Object Oriented PHP, MYSQLi and ending the course by building a CMS system similar to WordPress, Joomla or Drupal. Knowing PHP has allowed me to make enough money to stay home and make courses like this one for students all over the world.\n\n### Course Features\n\n#### Section 1\n- Become an advanced, confident, and modern JavaScript developer from scratch.\n- Have an intermediate skill level of Python programming.\n- Have a portfolio of various data analysis projects.\n- Use the numpy library to create and manipulate arrays.\n\n#### Section 2\n- Use the Jupyter Notebook Environment. JavaScript developer from scratch.\n- Use the pandas module with Python to create and structure data.\n- Have a portfolio of various data analysis projects.\n- Create data visualizations using matplotlib and seaborn.\n\nLorem ipsum dolor sit amet consectetur, adipisicing elit. Omnis, aliquam voluptas laudantium incidunt architecto nam excepturi provident rem laborum repellendus placeat neque aut doloremque ut ullam, veritatis nesciunt iusto officia alias, non est vitae. Eius repudiandae optio quam alias aperiam nemo nam tempora, dignissimos dicta excepturi ea quo ipsum omnis maiores perferendis commodi voluptatum facere vel vero. Praesentium quisquam iure veritatis, perferendis adipisci sequi blanditiis quidem porro eligendi fugiat facilis inventore amet delectus expedita deserunt ut molestiae modi laudantium, quia tenetur animi natus ea. Molestiae molestias ducimus pariatur et consectetur. Error vero, eum soluta delectus necessitatibus eligendi numquam hic at?",
            category="Programming",
            created_by=instructor.id,
            service_line_id=service_lines[0].name,
            expected_time_to_complete=10,
            approved_by=admin.id,
            approved_date=datetime.now(),
            status="approve",
        )
        course3 = Course(
            title="course3",
            description="Learn Python basics",
            category="Programming",
            created_by=instructor.id,
            service_line_id=service_lines[0].name,
            expected_time_to_complete=10,
            approved_by=admin.id,
            approved_date=datetime.now(),
            status="approve",
            tags="advanced,ml",
        )
        course4 = Course(
            title="course4",
            description="Learn Python basics",
            category="Programming",
            created_by=instructor.id,
            service_line_id=service_lines[0].name,
            expected_time_to_complete=10,
            approved_by=admin.id,
            approved_date=datetime.now(),
            status="approve",
        )
        course5 = Course(
            title="course5",
            description="Learn Python basics",
            category="Programming",
            created_by=admin.id,
            service_line_id=service_lines[0].name,
            expected_time_to_complete=10,
            approved_by=admin.id,
            approved_date=datetime.now(),
            status="approve",
        )
        course6 = Course(
            title="Advanced Data Science",
            description="Deep dive into data science techniques",
            category="Data Science",
            created_by=admin.id,
            service_line_id=service_lines[1].name,
            expected_time_to_complete=20,
            approved_by=admin.id,
            approved_date=datetime.now(),
            status="approve",
            tags="beginner,python",
        )

        db.add_all([course1, course2, course3, course4, course5, course6])
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
            expected_time_to_complete=134
        )
        content2 = Content(
            chapter_id=chapter1.id,
            title="Hello World",
            content_type="video",
            file_id=str(uuid.uuid4()),
            expected_time_to_complete=105
        )

        db.add_all([content1, content2])
        db.commit()

        # Create enrollments
        enrollment1 = Enrollment(
            user_id=employee.id,
            course_id=course1.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=121),
            year=datetime.now().year,
            status="Completed",
        )
        enrollment2 = Enrollment(
            user_id=employee.id,
            course_id=course3.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=32),
            year=datetime.now().year,
        )
        enrollment3 = Enrollment(
            user_id=employee.id,
            course_id=course4.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=12),
            year=datetime.now().year,
        )
        enrollment4 = Enrollment(
            user_id=employee.id,
            course_id=course5.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=45),
            year=datetime.now().year,
            status="Completed",
        )
        enrollment5 = Enrollment(
            user_id=employee.id,
            course_id=course6.id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=134),
            year=datetime.now().year,
        )

        db.add_all([enrollment1, enrollment2, enrollment3, enrollment4, enrollment5])
        db.commit()

        # Create progress
        progress1 = Progress(
            enrollment_id=enrollment1.id,
            chapter_id=chapter1.id,
            content_id=content1.id,
            completed_at=datetime.now(),
        )
        progress2 = Progress(
            enrollment_id=enrollment1.id,
            chapter_id=chapter2.id,
            content_id=content2.id,
            completed_at=datetime.now(),
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
            submitted_by=employee.id,
        )
        feedback2 = Feedback(
            user_id=employee.id,
            course_id=course2.id,
            description="Very informative.",
            rating=4,
            submitted_by=employee.id,
        )

        db.add_all([feedback1, feedback2])
        db.commit()

        # Create learning paths
        learning_path1 = LearningPath(
            name="Python Developer Path",
            service_line_id=service_lines[0].name,
            entity="Pierian"
        )
        learning_path1.courses.append(course1)
        learning_path1.courses.append(course2)
        learning_path1.courses.append(course3)
        db.add(learning_path1)
        db.commit()

        # # Add learning path enrollments
        # learning_path_enrollment1 = LearningPathEnrollment(
        #     user_id=employee.id,
        #     learning_path_id=learning_path1.id,
        #     enroll_date=datetime.now(),
        #     due_date=datetime.now() + timedelta(days=30),
        #     year=datetime.now().year,
        #     status="Enrolled",
        # )
        # db.add(learning_path_enrollment1)
        # db.commit()

        # Create certificates
        certificate1 = Certificate(
            user_id=employee.id,
            course_id=course1.id,
            issue_date=datetime.now()

            # certificate_url="http://example.com/certificates/certificate1.pdf"
        )
        certificate2 = Certificate(
            user_id=employee.id,
            course_id=course2.id,
            issue_date=datetime.now()
            # certificate_url="http://example.com/certificates/certificate2.pdf"
        )
        certificate3 = Certificate(
            user_id=employee.id,
            course_id=course3.id,
            issue_date=datetime.now()

            # certificate_url="http://example.com/certificates/certificate3.pdf"
        )

        db.add_all([certificate1, certificate2, certificate3])
        db.commit()
        print("Sample data created successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
