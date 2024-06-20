from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_current_user
from dependencies import get_db
from models import User, Enrollment, Progress
from schemas import DashStats

app = APIRouter(prefix="/stats", tags=["stats"])


@app.get("/dash", response_model=DashStats)
def dash_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Count of all enrollments
    enrolled_count = db.query(Enrollment) \
        .filter(Enrollment.user_id == current_user.id) \
        .count()

    # Count of all active courses (where there's some progress)
    active_count = db.query(Progress) \
        .join(Enrollment, Enrollment.id == Progress.enrollment_id) \
        .filter(Enrollment.user_id == current_user.id) \
        .distinct(Enrollment.course_id) \
        .count()

    # Count of all completed courses
    completed_count = db.query(Enrollment) \
        .filter(Enrollment.user_id == current_user.id) \
        .filter(Enrollment.status == "Completed") \
        .count()

    return {
        "enrolled_count": enrolled_count,
        "active_count": active_count,
        "completed_count": completed_count,
    }
