from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from auth import get_current_user
from dependencies import get_db
from models import User
from schemas import DashStats, DashInput

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
            e.course_id, e.status, e.completion_percentage, e.due_date, 
            c.expected_time_to_complete, c.category
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
    pending_courses_count = 0
    completed_courses_count = 0
    overdue_courses_count = 0
    technical_hours = 0
    non_technical_hours = 0

    current_time = datetime.now()

    for enrollment in enrollments:
        status = enrollment.status
        completion_percentage = enrollment.completion_percentage
        expected_time_to_complete = enrollment.expected_time_to_complete
        due_date = enrollment.due_date
        category = enrollment.category

        if status == "Completed":
            total_completed_hours += expected_time_to_complete
            completed_courses_count += 1
            if category == "Technical":
                technical_hours += expected_time_to_complete
            else:
                non_technical_hours += expected_time_to_complete
        else:
            completed_hours = (expected_time_to_complete * completion_percentage) / 100
            pending_hours = expected_time_to_complete - completed_hours
            total_completed_hours += completed_hours
            total_pending_hours += pending_hours
            pending_courses_count += 1
            if due_date and datetime.strptime(due_date, "%Y-%m-%d") < current_time:
                overdue_courses_count += 1
            if category == "Technical":
                technical_hours += completed_hours
            else:
                non_technical_hours += completed_hours

    compliance_status = technical_hours >= 50 and non_technical_hours >= 15

    result = {
        "total_completed_hours": total_completed_hours,
        "total_pending_hours": total_pending_hours,
        "pending_courses_count": pending_courses_count,
        "completed_courses_count": completed_courses_count,
        "overdue_courses_count": overdue_courses_count,
        "compliance_status": compliance_status,
        "technical_hours": technical_hours,
        "non_technical_hours": non_technical_hours,
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

        result.update(
            {
                "total_users": total_users,
                "total_courses": total_courses,
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

        result.update(
            {
                "total_users": total_users,
                "total_courses": total_courses,
            }
        )

    return DashStats(**result)
