from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func, extract

from datetime import datetime, timedelta

from auth import get_current_user
from config import complience_total_tech_learning_target, complience_total_non_tech_learning_target
from dependencies import get_db
from models import User, Enrollment, Progress, Course, LearningPath, ExternalCertification, Content
from schemas import DashStats, DashInput, DashStatsNew, CourseStats, InstructorDashStatsNew, AdminDashStatsNew, \
    StudyHoursResponse, MonthlyStudyHours
from dateutil.relativedelta import relativedelta

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
            if category == "technical":
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
            if category == "technical":
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


# Modify the get_weekly_activity function to get monthly activity data
def get_monthly_activity(start_date, end_date, db: Session, current_user_id: int):
    return (db.query(
        func.strftime('%Y-%m', Progress.completed_at).label('month'),
        func.count('*').label('count')
    ).join(Enrollment).filter(
        Enrollment.user_id == current_user_id,
        Progress.completed_at >= start_date,
        Progress.completed_at <= end_date
    ).group_by(func.strftime('%Y-%m', Progress.completed_at)).all())

@app.get("/dash/new/",
         response_model=Union[DashStatsNew, InstructorDashStatsNew, AdminDashStatsNew],
         )
def dash_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Define last month's time range
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    # Queries for current month and last month activities
    monthly_activity_data = get_monthly_activity(start_of_month, end_of_month, db, current_user.id)
    last_monthly_activity_data = get_monthly_activity(start_of_last_month, end_of_last_month, db, current_user.id)

    # Convert the query results to dictionaries
    monthly_activity = {month: count for month, count in monthly_activity_data}
    last_monthly_activity = {month: count for month, count in last_monthly_activity_data}

    # Additional code for calculating other stats
    completed_course_count = db.query(Enrollment).filter_by(user_id=current_user.id, status="Completed").count()
    active_course_count = db.query(Enrollment).filter_by(user_id=current_user.id, status="Active").count()
    pending_course_count = db.query(Enrollment).filter_by(user_id=current_user.id, status="Pending").count()

    active_courses = [
        CourseStats.from_orm(course) for course in current_user.courses_assigned if course.status == 'Enrolled'
    ]
    print(current_user.get_total_non_tech_learning_hours(current_user.id))
    if current_user.role_name == 'Employee':
        return DashStatsNew(
            completed_course_count=completed_course_count,
            active_course_count=active_course_count,
            pending_course_count=pending_course_count,
            monthly_learning_activity=monthly_activity,
            last_monthly_learning_activity=last_monthly_activity,
            my_progress=current_user.completion_percentage,
            active_courses=active_courses,
            certificates_count=current_user.certificates_count,
            total_learning_hours=current_user.total_learning_hours,
            total_tech_learning_hours=current_user.total_tech_learning_hours,
            total_non_tech_learning_hours=current_user.get_total_non_tech_learning_hours(current_user.id),
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
            monthly_learning_activity=monthly_activity,
            last_monthly_learning_activity=last_monthly_activity,
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
            monthly_learning_activity=monthly_activity,
            last_monthly_learning_activity=last_monthly_activity,
            my_progress=current_user.completion_percentage,
            active_courses=active_courses,
            certificates_count=current_user.certificates_count,
            total_learning_hours=current_user.total_learning_hours,
            total_tech_learning_hours=current_user.total_tech_learning_hours,
            total_non_tech_learning_hours=current_user.total_non_tech_learning_hours,
            complience_total_tech_learning_target=complience_total_tech_learning_target,
            complience_total_non_tech_learning_target=complience_total_non_tech_learning_target,
        )

@app.get("/the/last_api/", response_model=StudyHoursResponse)
def bad_api(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns the logged-in user's study hours for each of the last 12 months.
    Includes hours from both course progress and external certifications.
    """
    today = datetime.today()
    # Generate a list of the last 12 months in "YYYY-MM" format
    months = []
    for i in range(12):
        month_date = today - relativedelta(months=i)
        month_str = month_date.strftime("%Y-%m")
        months.append(month_str)
    months = sorted(months)  # Ensure chronological order

    # Initialize a dictionary with months as keys and 0 hours
    study_hours_dict = {month: 0.0 for month in months}
    start_date = (today - relativedelta(months=11)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (today + relativedelta(months=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Query 1: Progress Hours from Course Content
    progress_query = (
        db.query(
            extract('year', Progress.completed_at).label("year"),
            extract('month', Progress.completed_at).label("month"),
            func.sum(Content.expected_time_to_complete).label("hours")
        )
        .join(Enrollment, Progress.enrollment_id == Enrollment.id)
        .join(Content, Progress.content_id == Content.id)
        .join(User, Enrollment.user_id == User.id)
        .filter(
            User.counselor_id == current_user.id,
            Progress.completed_at >= start_date,
            Progress.completed_at < end_date
        )
        .group_by("year", "month")
    )
    progress_results = progress_query.all()

    for result in progress_results:
        month = result.month
        hours = float(result.hours) if result.hours else 0.0
        if month in study_hours_dict:
            study_hours_dict[month] += hours

    # Query 2: External Certification Hours
    certification_query = (
        db.query(
            func.strftime("%Y-%m", ExternalCertification.date_of_completion).label("month"),  # Use strftime for date formatting
            func.sum(ExternalCertification.hours).label("hours")
        )
        .join(User, ExternalCertification.uploaded_by_id == User.id)  # Explicit join
        .filter(
            User.counselor_id == current_user.id,
            ExternalCertification.date_of_completion >= start_date,
            ExternalCertification.date_of_completion < end_date,
            ExternalCertification.status == 'approved'  # Assuming only approved certifications count
        )
        .group_by("month")
    )
    certification_results = certification_query.all()

    for result in certification_results:
        month = result.month
        hours = float(result.hours) if result.hours else 0.0
        if month in study_hours_dict:
            study_hours_dict[month] += hours

    # Prepare the response data
    response_data = [
        MonthlyStudyHours(month=month, hours=study_hours_dict.get(month, 0.0))
        for month in months
    ]

    return StudyHoursResponse(data=response_data)




@app.get("/the/last_api_final/", response_model=StudyHoursResponse)
def bad_api(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns the logged-in user's study hours for each of the last 12 months.
    Includes hours from both course progress and external certifications.
    """
    today = datetime.today()
    # Generate a list of the last 12 months in "YYYY-MM" format
    months = []
    for i in range(12):
        month_date = today - relativedelta(months=i)
        month_str = month_date.strftime("%Y-%m")
        months.append(month_str)
    months = sorted(months)  # Ensure chronological order

    # Initialize a dictionary with months as keys and 0 hours
    study_hours_dict = {month: 0.0 for month in months}
    start_date = (today - relativedelta(months=11)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (today + relativedelta(months=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Query 1: Progress Hours from Course Content
    progress_query = (
        db.query(
            func.strftime("%Y-%m", Progress.completed_at).label("month"),  # Use strftime for date formatting
            func.sum(Content.expected_time_to_complete).label("hours")
        )
        .join(Enrollment, Progress.enrollment_id == Enrollment.id)
        .join(Content, Progress.content_id == Content.id)
        .join(User, Enrollment.user_id == User.id)
        .filter(
            User.counselor_id == current_user.id,
            Progress.completed_at >= start_date,
            Progress.completed_at < end_date
        )
        .group_by("month")
    )

    progress_results = progress_query.all()

    for result in progress_results:
        month = result.month
        hours = float(result.hours) if result.hours else 0.0
        if month in study_hours_dict:
            study_hours_dict[month] += hours

    # Query 2: External Certification Hours
    certification_query = (
        db.query(
            func.strftime("%Y-%m", ExternalCertification.date_of_completion).label("month"),  # Use strftime for date formatting
            func.sum(ExternalCertification.hours).label("hours")
        )
        .filter(
            ExternalCertification.uploaded_by.counselor_id == current_user.id,
            ExternalCertification.date_of_completion >= start_date,
            ExternalCertification.date_of_completion < end_date,
            ExternalCertification.status == 'approved'  # Assuming only approved certifications count
        )
        .group_by("month")
    )

    certification_results = certification_query.all()

    for result in certification_results:
        month = result.month
        hours = float(result.hours) if result.hours else 0.0
        if month in study_hours_dict:
            study_hours_dict[month] += hours

    # Prepare the response data
    response_data = [
        MonthlyStudyHours(month=month, hours=study_hours_dict.get(month, 0.0))
        for month in months
    ]

    return StudyHoursResponse(data=response_data)


