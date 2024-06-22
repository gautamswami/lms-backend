from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Import local modules
from auth import get_current_user
from crud import enroll_users
from dependencies import get_db
from models import Course, User, Enrollment
from schemas import (CourseFullDisplay, EnrollmentRequest)

app = APIRouter(tags=['course', 'enrollment'])


@app.post("/enroll/by/instructors/", status_code=201)
async def enroll_by_instructor(request: EnrollmentRequest, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    if current_user.role_name != "Instructor":
        raise HTTPException(status_code=403, detail="Only instructors can perform this action.")

    # Check if all users are counselees of the instructor
    counselees_ids = {user.id for user in current_user.counselees}
    if not set(request.user_ids).issubset(counselees_ids):
        raise HTTPException(status_code=403, detail="You can only enroll your own team members.")

    return enroll_users(request.course_id, request.user_ids, db)


@app.post("/enroll/by/admins/", status_code=201)
async def enroll_by_admin(request: EnrollmentRequest, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if current_user.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can perform this action.")

    # Check if all users belong to the admin's service line
    service_line_users = db.query(User).filter(User.service_line_id == current_user.service_line_id).all()
    service_line_user_ids = {user.id for user in service_line_users}
    if not set(request.user_ids).issubset(service_line_user_ids):
        raise HTTPException(status_code=403, detail="You can only enroll users within your service line.")

    return enroll_users(request.course_id, request.user_ids, db)


@app.get("/users/enrolled-courses", response_model=List[CourseFullDisplay])
async def get_enrolled_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enrolled_courses = db.query(Course).join(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    return enrolled_courses