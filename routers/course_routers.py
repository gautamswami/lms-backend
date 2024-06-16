from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path
from sqlalchemy.orm import Session, joinedload

from auth import get_current_user
from crud import enroll_users
from dependencies import get_db
from file_storage import FileStorage
from models import Course, Chapter, User, Content, Enrollment
from schemas import CourseCreate, CourseDisplay, ChapterCreate, ChapterDisplay, ContentDisplay, EnrollmentRequest

app = APIRouter(tags=['course'])


@app.post("/courses/", response_model=CourseDisplay)
def create_course(course: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role_name == "Employee":
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    new_course = Course(**course.dict(), created_by=current_user.id, service_line_id=current_user.service_line_id)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@app.get("/courses/", response_model=List[CourseDisplay])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).options(joinedload(Course.approver)).all()
    return courses


@app.get("/courses/{course_id}", response_model=CourseDisplay)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


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


@app.post("/chapters/{chapter_id}/content/", response_model=ContentDisplay)
async def create_content(chapter_id: int = Path(..., description="The ID of the chapter"), file: UploadFile = File(...),
                         db: Session = Depends(get_db)):
    file_storage = FileStorage()

    # Set type as "Course content" and use the file's original name as the title
    file_type = "Course content"
    title = file.filename
    content_type = file.content_type

    # Save the file using the storage class
    try:
        file_metadata = file_storage.save_file(file, db, type=file_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create new content record linked to the specified chapter
    new_content = Content(
        chapter_id=chapter_id,
        title=title,
        content_type=content_type,
        file_id=file_metadata.FileID
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return new_content


# __________________________________________________________________________________________________________

@app.post("/enroll/self/", status_code=201)
async def enroll_self(request: EnrollmentRequest,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if len(request.user_ids) != 1 or request.user_ids[0] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only enroll yourself.")

    return enroll_users(request.course_id, request.user_ids, db)


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
async def enroll_by_admin(request: EnrollmentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can perform this action.")

    # Check if all users belong to the admin's service line
    service_line_users = db.query(User).filter(User.service_line_id == current_user.service_line_id).all()
    service_line_user_ids = {user.id for user in service_line_users}
    if not set(request.user_ids).issubset(service_line_user_ids):
        raise HTTPException(status_code=403, detail="You can only enroll users within your service line.")

    return enroll_users(request.course_id, request.user_ids, db)


@app.get("/users/enrolled-courses", response_model=List[CourseDisplay])
async def get_enrolled_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enrolled_courses = db.query(Course).join(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    return enrolled_courses