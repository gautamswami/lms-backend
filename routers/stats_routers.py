from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timedelta

from auth import get_current_user
from config import complience_total_tech_learning_target, complience_total_non_tech_learning_target
from dependencies import get_db
from models import User, Enrollment, Progress, Course, LearningPath, ExternalCertification
from schemas import DashStats, DashInput, DashStatsNew, CourseStats, InstructorDashStatsNew, AdminDashStatsNew

app = APIRouter(prefix="/stats", tags=["stats"])


@app.post("/dash", response_model=DashStats)
def dash_stats(
        dash_input: DashInput,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    # Raw SQL to get user details from email
    user_query = text(
        """
        SELECT id, role_name, service_line_id FROM users WHERE email = :email
    """
    )

    user = db.execute(user_query, {"email": dash_input.email}).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id
    role_name = user.role_name
    service_line_id = user.service_line_id

    # Common statistics
    enrollments_query = text(
        """
        SELECT 
            e.id, e.course_id, e.status, e.due_date, 
            c.expected_time_to_complete, c.title, c.category
        FROM 
            enrollments e
        JOIN 
            courses c ON e.course_id = c.id
        WHERE 
            e.user_id = :user_id
    """
    )

    enrollments = db.execute(enrollments_query, {"user_id": user_id}).fetchall()

    total_completed_hours = 0
    total_pending_hours = 0
    pending_courses = []
    completed_courses = []
    overdue_courses = []
    technical_hours = 0
    non_technical_hours = 0

    current_time = datetime.now()

    for enrollment in enrollments:
        status = enrollment.status
        # TODO AKASH
        completion_percentage = db.query(Enrollment).filter(
            Enrollment.id == enrollment.id).one().calculated_completion_percentage
        expected_time_to_complete = enrollment.expected_time_to_complete
        course_title = enrollment.title
        due_date = enrollment.due_date
        category = enrollment.category

        if status == "Completed":
            total_completed_hours += expected_time_to_complete
            completed_courses.append(course_title)
            if category == "Technical":
                technical_hours += expected_time_to_complete
            else:
                non_technical_hours += expected_time_to_complete
        else:
            completed_hours = (expected_time_to_complete * completion_percentage) / 100
            pending_hours = expected_time_to_complete - completed_hours
            total_completed_hours += completed_hours
            total_pending_hours += pending_hours
            pending_courses.append(course_title)
            if due_date and datetime.strptime(due_date, "%Y-%m-%d") < current_time:
                overdue_courses.append(course_title)
            if category == "Technical":
                technical_hours += completed_hours
            else:
                non_technical_hours += completed_hours

    compliance_status = technical_hours >= 50 and non_technical_hours >= 15

    numeric_stats = {
        "total_completed_hours": total_completed_hours,
        "total_pending_hours": total_pending_hours,
        "pending_courses_count": len(pending_courses),
        "completed_courses_count": len(completed_courses),
        "overdue_courses_count": len(overdue_courses),
        "compliance_status": compliance_status,
        "technical_hours": technical_hours,
        "non_technical_hours": non_technical_hours,
    }

    details = {
        "pending_courses": pending_courses,
        "completed_courses": completed_courses,
        "overdue_courses": overdue_courses,
    }

    # Additional stats based on user role
    if role_name == "Instructor":
        # Additional stats for instructor
        total_users_query = text(
            """
            SELECT COUNT(DISTINCT e.user_id) AS total_users
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE c.created_by = :user_id
        """
        )

        total_users = db.execute(total_users_query, {"user_id": user_id}).scalar()

        total_courses_query = text(
            """
            SELECT COUNT(*) AS total_courses
            FROM courses
            WHERE created_by = :user_id
        """
        )

        total_courses = db.execute(total_courses_query, {"user_id": user_id}).scalar()

        courses_table_query = text(
            """
            SELECT c.title, AVG(f.rating) AS average_rating, COUNT(e.user_id) AS total_users
            FROM courses c
            LEFT JOIN feedbacks f ON c.id = f.course_id
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.created_by = :user_id
            GROUP BY c.id
        """
        )

        courses_table = db.execute(courses_table_query, {"user_id": user_id}).fetchall()

        courses_table_result = [
            {
                "title": row.title,
                "average_rating": row.average_rating,
                "total_users": row.total_users,
            }
            for row in courses_table
        ]

        numeric_stats.update(
            {
                "total_users": total_users,
                "total_courses": total_courses,
            }
        )

        details.update(
            {
                "courses_table": courses_table_result,
            }
        )

    elif role_name in ["Admin", "Super Admin"]:
        # Additional stats for admin/super_admin
        total_users_query = text(
            """
            SELECT COUNT(DISTINCT e.user_id) AS total_users
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            JOIN users u ON e.user_id = u.id
            WHERE u.service_line_id = :service_line_id
        """
        )

        total_users = db.execute(
            total_users_query, {"service_line_id": service_line_id}
        ).scalar()

        total_courses_query = text(
            """
            SELECT COUNT(*) AS total_courses
            FROM courses
            WHERE service_line_id = :service_line_id
        """
        )

        total_courses = db.execute(
            total_courses_query, {"service_line_id": service_line_id}
        ).scalar()

        courses_table_query = text(
            """
            SELECT c.title, AVG(f.rating) AS average_rating, COUNT(e.user_id) AS total_users
            FROM courses c
            LEFT JOIN feedbacks f ON c.id = f.course_id
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.service_line_id = :service_line_id
            GROUP BY c.id
        """
        )

        courses_table = db.execute(
            courses_table_query, {"service_line_id": service_line_id}
        ).fetchall()

        courses_table_result = [
            {
                "title": row.title,
                "average_rating": row.average_rating,
                "total_users": row.total_users,
            }
            for row in courses_table
        ]

        numeric_stats.update(
            {
                "total_users": total_users,
                "total_courses": total_courses,
            }
        )

        details.update(
            {
                "courses_table": courses_table_result,
            }
        )

    return DashStats(numeric_stats=numeric_stats, details=details)


@app.get("/dash/new",
         response_model=Union[DashStatsNew, InstructorDashStatsNew, AdminDashStatsNew],
         )
def dash_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Define last week's time range
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = start_of_week - timedelta(days=1)

    # Queries for current week and last week activities
    def get_weekly_activity(start_date, end_date):
        return (db.query(
            func.date(Progress.completed_at).label('day'),
            func.count('*').label('count')
        ).join(Enrollment).filter(
            Enrollment.user_id == current_user.id,
            Progress.completed_at >= start_date,
            Progress.completed_at <= end_date
        ).group_by(func.date(Progress.completed_at)).all())

    weekly_activity_data = get_weekly_activity(start_of_week, end_of_week)
    last_weekly_activity_data = get_weekly_activity(start_of_last_week, end_of_last_week)

    # Convert the query results to dictionaries
    weekly_activity = {datetime.strptime(day, '%Y-%m-%d').strftime('%a'): count for day, count in weekly_activity_data}
    last_weekly_activity = {datetime.strptime(day, '%Y-%m-%d').strftime('%a'): count for day, count in last_weekly_activity_data}

    # Additional code for calculating other stats
    completed_course_count = db.query(Enrollment).filter_by(user_id=current_user.id, status="Completed").count()
    active_course_count = db.query(Enrollment).filter_by(user_id=current_user.id, status="Active").count()
    pending_course_count = db.query(Enrollment).filter_by(user_id=current_user.id, status="Pending").count()

    active_courses = [
        CourseStats.from_orm(course) for course in current_user.courses_assigned if course.status == 'Enrolled'
    ]

    print(current_user.role_name)
    if current_user.role_name == 'Employee':
        return DashStatsNew(
            completed_course_count=completed_course_count,
            active_course_count=active_course_count,
            pending_course_count=pending_course_count,
            weekly_learning_activity=weekly_activity,
            last_weekly_learning_activity=last_weekly_activity,
            my_progress=current_user.completion_percentage,
            active_courses=active_courses,
            certificates_count=current_user.certificates_count,
            total_learning_hours=current_user.total_learning_hours,
            total_tech_learning_hours=current_user.total_tech_learning_hours,
            total_non_tech_learning_hours=current_user.total_non_tech_learning_hours,
            complience_total_tech_learning_target=complience_total_tech_learning_target,
            complience_total_non_tech_learning_target=complience_total_non_tech_learning_target,
        )
    elif current_user.role_name == 'Instructor':
        total_users_count = db.query(User).filter_by(counselor_id=current_user.id).count()
        total_courses_count = db.query(Course).count()
        approval_pending_courses_count = db.query(Course).filter_by(created_by=current_user.id, status="approval pending").count()
        approved_courses_count = db.query(Course).filter_by(created_by=current_user.id, status="approve").count()

        return InstructorDashStatsNew(
            total_users_count=total_users_count,
            total_courses_count=total_courses_count,
            approval_pending_courses_count=approval_pending_courses_count,
            approved_courses_count=approved_courses_count,
            completed_course_count=completed_course_count,
            active_course_count=active_course_count,
            pending_course_count=pending_course_count,
            weekly_learning_activity=weekly_activity,
            last_weekly_learning_activity=last_weekly_activity,
            my_progress=current_user.completion_percentage,
            active_courses=active_courses,
            certificates_count=current_user.certificates_count,
            total_learning_hours=current_user.total_learning_hours,
            total_tech_learning_hours=current_user.total_tech_learning_hours,
            total_non_tech_learning_hours=current_user.total_non_tech_learning_hours,
            complience_total_tech_learning_target=complience_total_tech_learning_target,
            complience_total_non_tech_learning_target=complience_total_non_tech_learning_target,
        )
    else:
        print("inside this")
        total_users_count = db.query(User).filter_by(service_line_id=current_user.service_line_id).count()
        total_courses_count = db.query(Course).count()
        approval_pending_external_courses_count = (
            db.query(ExternalCertification)
            .join(User, ExternalCertification.uploaded_by_id == User.id)
            .filter(User.service_line_id == current_user.service_line_id, ExternalCertification.status == "pending")
            .count()
        )
        approval_pending_courses_count = db.query(Course).filter_by(service_line_id=current_user.service_line_id, status="approval pending").count()
        approved_courses_count = db.query(Course).filter_by(service_line_id=current_user.service_line_id, status="approve").count()
        total_learning_path_count = db.query(LearningPath).filter_by().count()

        return AdminDashStatsNew(
            total_users_count=total_users_count,
            total_courses_count=total_courses_count,
            approval_pending_external_courses_count=approval_pending_external_courses_count,
            approval_pending_courses_count=approval_pending_courses_count,
            approved_courses_count=approved_courses_count,
            total_learning_path_count=total_learning_path_count,
            completed_course_count=completed_course_count,
            active_course_count=active_course_count,
            pending_course_count=pending_course_count,
            weekly_learning_activity=weekly_activity,
            last_weekly_learning_activity=last_weekly_activity,
            my_progress=current_user.completion_percentage,
            active_courses=active_courses,
            certificates_count=current_user.certificates_count,
            total_learning_hours=current_user.total_learning_hours,
            total_tech_learning_hours=current_user.total_tech_learning_hours,
            total_non_tech_learning_hours=current_user.total_non_tech_learning_hours,
            complience_total_tech_learning_target=complience_total_tech_learning_target,
            complience_total_non_tech_learning_target=complience_total_non_tech_learning_target,
        )
