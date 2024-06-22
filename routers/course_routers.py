from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path
from sqlalchemy.orm import Session, joinedload

# Import local modules
from auth import get_current_user
from crud import enroll_users
from dependencies import get_db
from file_storage import FileStorage
from models import Course, Chapter, User, Content, Enrollment, Progress
from schemas import (CourseCreate, CourseFullDisplay, ChapterCreate, ChapterDisplay,
                     ContentDisplay, EnrollmentRequest, CourseSortDisplay, CourseUpdate, ContentCreate)

app = APIRouter(tags=['course'])


# ------------------- Course Operations -------------------

# Create a new course
@app.post("/courses", response_model=CourseFullDisplay)
def create_course(course: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role_name == "Employee":
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    if course.service_line_id is None:
        course.service_line_id = current_user.service_line_id
    new_course = Course(**course.dict(), created_by=current_user.id)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


# Retrieve all courses
@app.get("/courses", response_model=List[CourseSortDisplay])
def get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(current_user.first_name)
    courses = db.query(Course).options(joinedload(Course.approver)).all()
    return courses


# Retrieve courses the current user is enrolled in
@app.get("/courses/enrolled", response_model=List[CourseSortDisplay])
def get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    courses = [enrollment.course for enrollment in enrollments]
    return courses


# Retrieve active courses with user's progress
@app.get("/courses/active", response_model=List[CourseSortDisplay])
def get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    progresses = db.query(Progress) \
        .filter(Enrollment.user_id == current_user.id) \
        .all()
    courses = {progress.enrollment.course for progress in progresses}
    return courses


# Retrieve completed courses
@app.get("/courses/completed", response_model=List[CourseFullDisplay])
def get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enrollments = db.query(Enrollment) \
        .filter(Enrollment.user_id == current_user.id) \
        .filter(Enrollment.status == "Completed") \
        .all()
    courses = [enrollment.course for enrollment in enrollments]
    return courses


# Retrieve a specific course by ID
@app.get("/courses/{course_id}", response_model=CourseFullDisplay)
def get_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@app.put("/courses/{course_id}", response_model=CourseSortDisplay)
def update_question(course_id: int, question_data: CourseUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    if current_user.role_name == "Employee":
        raise HTTPException(status_code=403, detail="Only Employee can not update courses")
    course = db.query(Course).filter(Course.id == course_id).first()

    if current_user.role_name == "Instructor" and current_user.id != course.created_by:
        raise HTTPException(status_code=403, detail="Instructors can only update it's own courses")
    if not course:
        raise HTTPException(status_code=404, detail="Question not found")

    for var, value in vars(question_data).items():
        if value is not None:
            setattr(course, var, value)

    db.commit()
    return course


@app.delete("/courses/{course_id}", status_code=204)
def update_question(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # DELETE course by id only if there is no Enrollments, delete all  Chapters, delete all content
    # Check for any existing enrollments for the course
    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).first()
    if enrollments:
        raise HTTPException(status_code=400, detail="Cannot delete course with active enrollments")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Question not found")

    for chapter in course.chapters:
        for content in chapter.contents:
            db.delete(content)
        for questions in chapter.questions:
            db.delete(questions)
        db.delete(chapter)

    for questions in course.questions:
        try:
            db.delete(questions)
        except:
            pass
    db.delete(course)
    db.commit()
    return {"message": "Question deleted successfully"}


# ------------------- Chapter Operations -------------------


# Create a new chapter for a course
@app.post("/courses/chapters/", response_model=ChapterDisplay)
def create_chapter(chapter: ChapterCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == chapter.course_id).first()
    if not course or course.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")
    new_chapter = Chapter(**chapter.dict())
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


# ------------------- Content Operations -------------------

# Upload content to a specific chapter
@app.post("/chapters/{chapter_id}/content/", response_model=ContentDisplay)
async def create_content(
        content_data: ContentCreate,
        chapter_id: int = Path(..., description="The ID of the chapter"),
        db: Session = Depends(get_db)):
    file_storage = FileStorage()

    # Save the file using the storage class
    try:
        file_metadata = file_storage.save_file(content_data.file, db, type="Course content")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create new content record linked to the specified chapter
    new_content = Content(
        chapter_id=chapter_id,
        title=content_data.title,
        content_type=content_data.file.content_type,
        file_id=file_metadata.FileID
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return new_content


# ------------------- Enrollment Operations -------------------

# Enroll the current user into a course
@app.post("/enroll/self/", status_code=201)
async def enroll_self(request: EnrollmentRequest,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if len(request.user_ids) != 1 or request.user_ids[0] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only enroll yourself.")

    return enroll_users(request.course_id, request.user_ids, db)


@app.patch("/courses/{course_id}/approve")
def approve_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role_name in ["Employee", "Instructor"]:
        raise HTTPException(status_code=403, detail="Only admins can approve courses")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status == "approve":
        raise HTTPException(status_code=404, detail="already approved")

    course.status = "approve"
    course.approved_by = current_user.id
    course.approved_date = datetime.now()
    db.commit()
    return {"message": "Course approved successfully"}


@app.patch("/courses/{course_id}/reject")
def approve_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role_name in ["Employee", "Instructor"]:
        raise HTTPException(status_code=403, detail="Only admins can approve courses")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status == "approve":
        raise HTTPException(status_code=404, detail="already approved")

    course.status = "reject"
    course.approved_by = current_user.id
    course.approved_date = datetime.now()
    db.commit()
    return {"message": "Course reject successfully"}


@app.post("/courses/{course_id}/thumbnail", status_code=200)
async def upload_course_thumbnail(course_id: int = Path(..., description="The ID of the course"),
                                  file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if the file is an image
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload an image.")

    file_storage = FileStorage()

    # Save the file using the storage class
    try:
        file_metadata = file_storage.save_file(file, db, type="thumbnail")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Fetch the course and update its thumbnail_file_id
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.thumbnail_file_id = file_metadata.FileID
    db.commit()

    return {"message": "Thumbnail updated successfully.", "file_id": file_metadata.FileID}

# __________________________________________________________________________________________________________
