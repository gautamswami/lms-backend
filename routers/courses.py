from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from models import Course, Chapter, Enrollment, User
from schemas import CourseCreate, CourseDisplay, ChapterCreate, ChapterDisplay, EnrollmentCreate, EnrollmentDisplay
from dependencies import get_db
from typing import List

router = APIRouter()


@router.post("/courses/", response_model=CourseDisplay)
def create_course(course: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.RoleName != "Instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    new_course = Course(**course.dict(), InstructorID=current_user.UserID, DepartmentID=current_user.DepartmentID)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@router.patch("/courses/{course_id}/approve")
def approve_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.RoleName != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can approve courses")
    course = db.query(Course).filter(Course.CourseID == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.IsApproved = True
    db.commit()
    return {"message": "Course approved successfully"}


@router.post("/courses/{course_id}/chapters/", response_model=ChapterDisplay)
def create_chapter(course_id: int, chapter: ChapterCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.CourseID == course_id).first()
    if not course or course.InstructorID != current_user.UserID:
        raise HTTPException(status_code=403, detail="Operation not permitted")
    new_chapter = Chapter(**chapter.dict(), CourseID=course_id)
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


@router.post("/enrollments/", response_model=EnrollmentDisplay)
def enroll_course(enrollment: EnrollmentCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    if current_user.RoleName != "Employee":
        raise HTTPException(status_code=403, detail="Only employees can enroll in courses")
    new_enrollment = Enrollment(**enrollment.dict(), UserID=current_user.UserID)
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment


@router.get("/courses/", response_model=List[CourseDisplay])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return courses


@router.get("/courses/{course_id}", response_model=CourseDisplay)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.CourseID == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/courses/{course_id}/chapters/", response_model=List[ChapterDisplay])
def get_chapters(course_id: int, db: Session = Depends(get_db)):
    chapters = db.query(Chapter).filter(Chapter.CourseID == course_id).all()
    return chapters
