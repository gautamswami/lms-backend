from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

# Import local modules
from auth import get_current_user
from crud import enroll_users, get_completed_content_ids
from dependencies import get_db
from models import (
    Course,
    User,
    Enrollment,
    Progress,
    Content,
    Certificate,
    Chapter,
    Questions,
    QuizCompletions,
)
from schemas import EnrollmentRequest, EnrolledCourseDisplay

app = APIRouter(tags=["course", "enrollment"])


# Enroll the current user into a course
@app.post("/enroll/self/", status_code=201)
async def enroll_self(
    request: EnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(request.user_ids) != 1 or request.user_ids[0] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only enroll yourself.")
    course = db.query(Course).filter(Course.id == request.user_ids[0]).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status != "approve":
        raise HTTPException(status_code=404, detail="Course is not approved yet")

    return enroll_users(request.course_id, request.user_ids, db)


@app.post("/enroll/by/instructors/", status_code=201)
async def enroll_by_instructor(
    request: EnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role_name != "Instructor":
        raise HTTPException(
            status_code=403, detail="Only instructors can perform this action."
        )

    # Check if all users are counselees of the instructor
    counselees_ids = {user.id for user in current_user.counselees}
    if not set(request.user_ids).issubset(counselees_ids):
        raise HTTPException(
            status_code=403, detail="You can only enroll your own team members."
        )
    course = db.query(Course).filter(Course.id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status != "approve":
        raise HTTPException(status_code=404, detail="Course is not approved yet")

    return enroll_users(request.course_id, request.user_ids, db)


@app.post("/enroll/by/admins/", status_code=201)
async def enroll_by_admin(
    request: EnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role_name not in ["Admin", "Super Admin"]:
        raise HTTPException(
            status_code=403, detail="Only admins can perform this action."
        )

    # Check if all users belong to the admin's service line
    # service_line_users = (
    #     db.query(User)
    #     .filter(User.service_line_id == current_user.service_line_id)
    #     .all()
    # )
    # service_line_user_ids = {user.id for user in service_line_users}
    # if not set(request.user_ids).issubset(service_line_user_ids):
    #     raise HTTPException(
    #         status_code=403,
    #         detail="You can only enroll users within your service line.",
    #     )
    course = db.query(Course).filter(Course.id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status != "approve":
        raise HTTPException(status_code=404, detail="Course is not approved yet")

    return enroll_users(request.course_id, request.user_ids, db)


@app.get("/users/enrolled-courses", response_model=List[EnrolledCourseDisplay])
async def get_enrolled_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Retrieve courses with their enrollments directly, making use of the joined load for efficiency
    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id)
        .options(joinedload(Course.enrollments))
        .all()
    )

    # Prepare the response by enriching the course data with enrollment-specific properties
    response = []
    for course in enrolled_courses:
        for enrollment in course.enrollments:
            course_display = EnrolledCourseDisplay.from_orm(course)
            course_display.completed_hours = enrollment.completed_hours
            course_display.completion_percentage = enrollment.completion_percentage
            response.append(course_display)

    return response


@app.put("/mark_as_done/{content_id}/")
async def mark_as_done(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Fetch content and its related chapter and check for user enrollment in one query
        content = (
            db.query(Content)
            .options(joinedload(Content.chapter))
            .filter(Content.id == content_id)
            .one_or_none()
        )
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Check if the current user is enrolled in the course related to the content
        enrollment = (
            db.query(Enrollment)
            .join(Chapter, Chapter.course_id == Enrollment.course_id)
            .join(Content, Content.chapter_id == Chapter.id)
            .filter(Enrollment.user_id == current_user.id, Content.id == content.id)
            .one_or_none()
        )
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        # Update or create progress
        progress = (
            db.query(Progress)
            .filter(
                Progress.enrollment_id == enrollment.id,
                Progress.content_id == content_id,
                Progress.chapter_id
                == content.chapter_id,  # Ensure chapter_id is correct in your model
            )
            .one_or_none()
        )

        if not progress:
            progress = Progress(
                enrollment_id=enrollment.id,
                chapter_id=content.chapter_id,
                content_id=content_id,
                completed_at=datetime.now(),
            )
            db.add(progress)
        else:
            progress.completed_at = datetime.now()
        db.commit()
        db.refresh(enrollment)
        # Check if all contents in the course are completed to update the status
        remaining_contents = (
            db.query(Content)
            .join(Chapter)
            .outerjoin(
                Progress,
                and_(
                    Progress.content_id == Content.id,
                    Progress.enrollment_id == enrollment.id,
                ),
            )
            .filter(
                Chapter.course_id == enrollment.course_id,
                Progress.completed_at.is_(None),
            )
            .count()
        )
        # Check if all quizzes related to the course are completed
        pending_quizzes = (
            db.query(Questions)
            .join(Course, Course.id == Questions.course_id)
            .outerjoin(
                QuizCompletions,
                and_(
                    QuizCompletions.question_id == Questions.id,
                    QuizCompletions.enrollment_id == enrollment.id,
                    QuizCompletions.correct_answer == True,
                ),
            )
            .filter(
                Course.id == enrollment.course_id,
                QuizCompletions.id.is_(None),  # No completion record for this question
            )
            .count()
        )
        if remaining_contents == 0 and pending_quizzes == 0:
            enrollment.status = "Completed"
            db.add(Certificate(user_id=current_user.id, course_id=enrollment.course_id))
            db.commit()
            return {"message": "Course is completed and certificate is added "}

        return {"message": "Progress updated successfully",
                "pending_quizzes": pending_quizzes,
                "remaining_contents": remaining_contents,
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException as http_exec:
        db.rollback()
        raise http_exec
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content_status/{chapter_id}", response_model=List[int])
async def mark_as_done(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Query for existing progress that matches the content_id and the current user
        completed_content_ids = get_completed_content_ids(
            current_user.id, chapter_id, db
        )
        return completed_content_ids
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
