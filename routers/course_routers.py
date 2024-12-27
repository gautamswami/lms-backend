import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Path, Form
from sqlalchemy import exists
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func, and_, or_

# Import local modules
from auth import get_current_user
from crud import enroll_users
from dependencies import get_db
from file_storage import FileStorage
from models import (
    Course,
    Chapter,
    User,
    Content,
    Enrollment,
    Questions,
    Certificate,
    QuizCompletions,
)
from schemas import (
    CourseCreate,
    CourseFullDisplay,
    ChapterCreate,
    ChapterDisplay,
    ContentDisplay,
    EnrollmentRequest,
    CourseSortDisplay,
    CourseUpdate,
    CertificateDisplay,
    EnrolledCourseDisplay,
    ListCoursesDisplay,
)

app = APIRouter(tags=["course"])


# ------------------- Course Operations -------------------


@app.post("/courses/", response_model=CourseFullDisplay)
async def create_course(
    course_data: CourseCreate,  # Assume JSON data is submitted
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role_name == "Employee":
        raise HTTPException(
            status_code=403, detail="Only instructors can create courses"
        )

    if course_data.service_line_id is None:
        course_data.service_line_id = current_user.service_line_id

    new_course = Course(
        **course_data.dict(exclude={"chapters"}), created_by=current_user.id
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    for chapter_data in course_data.chapters:
        new_chapter = Chapter(
            **chapter_data.dict(exclude={"quizzes"}),  # Exclude contents entirely
            course_id=new_course.id,
        )
        db.add(new_chapter)
        db.commit()
        db.refresh(new_chapter)

        for quiz_data in chapter_data.quizzes:
            new_question = Questions(chapter_id=new_chapter.id, **quiz_data.dict())
            db.add(new_question)
            db.commit()

    course = db.query(Course).filter(Course.id == new_course.id).first()
    course_display = CourseFullDisplay.from_orm(course)
    course_display.is_enrolled = False
    return course_display


# @app.put("/courses/{course_id}/", response_model=CourseFullDisplay)
# async def update_course(
#         course_id: int,
#         updated_course_data: CourseCreate,  # Assume JSON data for the entire course including chapters and quizzes
#         db: Session = Depends(get_db),
#         current_user: User = Depends(get_current_user),
# ):
#     # Retrieve the existing course
#     course = db.query(Course).filter(Course.id == course_id).first()
#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")
#
#     # Update course properties if necessary
#     for var, value in updated_course_data.dict(exclude={"chapters"}).items():
#         if value is not None:
#             setattr(course, var, value)
#
#     db.commit()
#
#     # Assuming all chapters are to be replaced with new ones provided in updated_course_data
#     # Remove existing chapters first
#     db.query(Chapter).filter(Chapter.course_id == course_id).delete()
#     db.commit()
#
#     # Add new chapters
#     for chapter_data in updated_course_data.chapters:
#         # Explicitly set the course_id here and exclude it from the dict to avoid conflict
#         new_chapter = Chapter(
#             **chapter_data.dict(
#                 exclude={"course_id"}
#             ),  # Ensure 'course_id' is excluded
#             course_id=course_id,
#         )
#         db.add(new_chapter)
#         db.commit()
#         db.refresh(new_chapter)
#
#     # Refresh the course instance to load updated data
#     db.refresh(course)
#     return course


@app.get("/courses/", response_model=List[CourseSortDisplay])
def get_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Use a subquery to check if the user is enrolled in each course
    subquery = (
        db.query(Enrollment.course_id)
        .filter(Enrollment.user_id == current_user.id)
        .subquery()
    )

    # Query all courses and check each one against the subquery for enrollment
    courses = (
        db.query(
            Course, exists().where(Course.id == subquery.c.course_id).correlate(Course)
        )
        .options(joinedload(Course.approver))
        .all()
    )
    result = []
    for course, is_enrolled in courses:
        course_ = CourseSortDisplay.from_orm(course)
        course_.is_enrolled = is_enrolled
        result.append(course_)

    return result


# Retrieve courses the current user is enrolled in (Pending status)
@app.get("/courses/enrolled/", response_model=List[EnrolledCourseDisplay])
def get_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Retrieve courses with "Pending" status
    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id)
        .filter(Enrollment.status == "Pending")
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


# Retrieve active courses with user's progress (Active status)
@app.get("/courses/active/", response_model=List[ListCoursesDisplay])
def get_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Retrieve courses with "Active" status
    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id)
        .filter(Enrollment.status == "Active")
        .options(joinedload(Course.enrollments))
        .all()
    )

    # Prepare the response by enriching the course data with enrollment-specific properties
    response = []
    for course in enrolled_courses:
        for enrollment in course.enrollments:
            course_display = ListCoursesDisplay.from_orm(course)
            course_display.completed_hours = enrollment.completed_hours
            course_display.completion_percentage = enrollment.completion_percentage
            course_display.total_questions = len(course.questions)
            course_display.completed_questions = (
                db.query(func.count(QuizCompletions.id))
                .filter(
                    QuizCompletions.enrollment_id == enrollment.id,
                    QuizCompletions.correct_answer == True,
                )
                .scalar()
            )
            response.append(course_display)

    return response


# Retrieve completed courses (Completed status)
@app.get("/courses/completed/", response_model=List[ListCoursesDisplay])
def get_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Retrieve courses with "Completed" status
    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == current_user.id)
        .filter(Enrollment.status == "Completed")
        .options(joinedload(Course.enrollments))
        .all()
    )

    # Prepare the response by enriching the course data with enrollment-specific properties
    response = []
    for course in enrolled_courses:
        for enrollment in course.enrollments:
            course_display = ListCoursesDisplay.from_orm(course)
            course_display.completed_hours = enrollment.completed_hours
            course_display.completion_percentage = enrollment.completion_percentage
            course_display.total_questions = len(course.questions)
            course_display.completed_questions = (
                db.query(func.count(QuizCompletions.id))
                .filter(
                    QuizCompletions.enrollment_id == enrollment.id,
                    QuizCompletions.correct_answer == True,
                )
                .scalar()
            )
            response.append(course_display)

    return response


# # Retrieve a specific course by ID
# @app.get("/courses/{course_id}/", response_model=CourseFullDisplay)
# def get_course(
#         course_id: int,
#         db: Session = Depends(get_db),
#         current_user: User = Depends(get_current_user),
# ):
#     course = db.query(Course).filter(Course.id == course_id).first()
#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")
#     return course


@app.post("/coursesupdate/{course_id}/", response_model=CourseFullDisplay)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role_name == "Employee":
        raise HTTPException(status_code=403, detail="Employees cannot update courses")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role_name == "Instructor" and current_user.id != course.created_by:
        raise HTTPException(
            status_code=403, detail="Instructors can only update their own courses"
        )

    # Update course properties
    for var, value in vars(course_data).items():
        if var == "chapters" or var == "questions":
            continue
        elif value is not None:
            setattr(course, var, value)

    db.commit()

    # Update course-level questions
    if course_data.questions:
        existing_question_ids = {question.id for question in course.questions}
        updated_question_ids = {
            question.id for question in course_data.questions if question.id
        }

        # Delete questions that are no longer present in the update request
        questions_to_delete = existing_question_ids - updated_question_ids
        for question_id in questions_to_delete:
            question = db.query(Questions).filter(Questions.id == question_id).first()
            if question:
                db.delete(question)
                db.commit()

        # Create or update questions
        for q in course_data.questions:
            if q.id:
                # Update existing question
                question = db.query(Questions).filter(Questions.id == q.id).first()
                if question:
                    for var, value in vars(q).items():
                        if var == "id":
                            continue
                        elif value is not None:
                            setattr(question, var, value)
                    db.commit()
            else:
                # Create new question
                new_question = Questions(
                    **q.dict(exclude={"id", "course_id"}),
                    course_id=course_id,
                    added_by=current_user.id,
                )
                db.add(new_question)
                db.commit()
                db.refresh(new_question)
                q.id = new_question.id

    if course_data.chapters:
        existing_chapter_ids = {chapter.id for chapter in course.chapters}
        updated_chapter_ids = {
            chapter.id for chapter in course_data.chapters if chapter.id
        }

        # Delete chapters that are no longer present in the update request
        chapters_to_delete = existing_chapter_ids - updated_chapter_ids
        for chapter_id in chapters_to_delete:
            chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
            if chapter:
                for content in chapter.contents:
                    db.delete(content)
                for question in chapter.questions:
                    db.delete(question)
                db.delete(chapter)
                db.commit()

        # Create or update chapters
        for c in course_data.chapters:
            if c.id:
                # Update existing chapter
                chapter = db.query(Chapter).filter(Chapter.id == c.id).first()
                if chapter:
                    for var, value in vars(c).items():
                        if var == "id" or var == "contents" or var == "questions":
                            continue
                        elif value is not None:
                            setattr(chapter, var, value)
                    db.commit()
            else:
                # Create new chapter
                new_chapter = Chapter(
                    **c.dict(exclude={"id", "contents", "questions"}),
                    course_id=course_id,
                )
                db.add(new_chapter)
                db.commit()
                db.refresh(new_chapter)
                c.id = new_chapter.id

            # Handle contents
            existing_content_ids = {content.id for content in chapter.contents}
            updated_content_ids = {content.id for content in c.contents if content.id}

            # Delete contents that are no longer present in the update request
            contents_to_delete = existing_content_ids - updated_content_ids
            for content_id in contents_to_delete:
                content = db.query(Content).filter(Content.id == content_id).first()
                if content:
                    db.delete(content)
                    db.commit()

            # Create or update contents
            for content_data in c.contents:
                if content_data.id:
                    # Update existing content
                    content = (
                        db.query(Content).filter(Content.id == content_data.id).first()
                    )
                    if content:
                        for var, value in vars(content_data).items():
                            if var == "id":
                                continue
                            elif value is not None:
                                setattr(content, var, value)
                        db.commit()
                else:
                    # Create new content
                    new_content = Content(
                        **content_data.dict(exclude={"id", "chapter_id"}),
                        chapter_id=c.id,
                    )
                    db.add(new_content)
                    db.commit()
                    db.refresh(new_content)
                    content_data.id = new_content.id

            # Handle chapter questions
            existing_question_ids = {question.id for question in chapter.questions}
            updated_question_ids = {
                question.id for question in c.questions if question.id
            }

            # Delete questions that are no longer present in the update request
            questions_to_delete = existing_question_ids - updated_question_ids
            for question_id in questions_to_delete:
                question = (
                    db.query(Questions).filter(Questions.id == question_id).first()
                )
                if question:
                    db.delete(question)
                    db.commit()

            # Create or update questions
            for question_data in c.questions:
                if question_data.id:
                    # Update existing question
                    question = (
                        db.query(Questions)
                        .filter(Questions.id == question_data.id)
                        .first()
                    )
                    if question:
                        for var, value in vars(question_data).items():
                            if var == "id":
                                continue
                            elif value is not None:
                                setattr(question, var, value)
                        db.commit()
                else:
                    # Create new question
                    new_question = Questions(
                        **question_data.dict(exclude={"id"}), chapter_id=c.id
                    )
                    db.add(new_question)
                    db.commit()
                    db.refresh(new_question)
                    question_data.id = new_question.id

    db.refresh(course)
    return CourseFullDisplay.from_orm(course)


@app.post("/courses_delete/{course_id}/", status_code=204)
def update_question(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # DELETE course by id only if there is no Enrollments, delete all  Chapters, delete all content
    # Check for any existing enrollments for the course
    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).first()
    if enrollments:
        raise HTTPException(
            status_code=400, detail="Cannot delete course with active enrollments"
        )

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
    return {"message": "deleted successfully"}


# ------------------- Chapter Operations -------------------


# Create a new chapter for a course
@app.post("/courses/chapters/", response_model=ChapterDisplay)
def create_chapter(
    chapter: ChapterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == chapter.course_id).first()
    if not course or course.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")
    new_chapter = Chapter(**chapter.dict())
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


# ------------------- Content Operations -------------------


@app.post("/chapters/{chapter_id}/content/", response_model=List[ContentDisplay])
async def create_content(
    chapter_id: int,
    titles_json: str = Form(...),  # Receive JSON-encoded titles as a string
    expected_time_to_complete: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    try:
        titles = json.loads(titles_json)  # Deserialize JSON string into a Python list
        expected_time_to_complete = json.loads(expected_time_to_complete)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for titles.")

    if len(files) != len(titles):
        raise HTTPException(
            status_code=400, detail="The number of titles and files must match."
        )
    if len(files) != len(expected_time_to_complete):
        raise HTTPException(
            status_code=400,
            detail="The number of titles and expected_times must match.",
        )

    responses = []
    for idx, file in enumerate(files):
        file_storage = FileStorage()

        try:
            file_metadata = file_storage.save_file(file, db, type="Course content")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        new_content = Content(
            chapter_id=chapter_id,
            title=titles[idx],  # Use the corresponding title from the deserialized list
            expected_time_to_complete=expected_time_to_complete[idx],
            content_type=file.content_type,
            file_id=file_metadata.FileID,
        )
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
        responses.append(new_content)

    return responses


# ------------------- Enrollment Operations -------------------


# Enroll the current user into a course
@app.post("/enroll/self/", status_code=201)
async def enroll_self(
    request: EnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(request.user_ids) != 1 or request.user_ids[0] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only enroll yourself.")

    return enroll_users(request.course_id, request.user_ids, db)


@app.post("/courseapprove/{course_id}/approve")
def approve_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@app.post("/coursereject/{course_id}/reject")
def approve_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
async def upload_course_thumbnail(
    course_id: int = Path(..., description="The ID of the course"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Check if the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Please upload an image."
        )

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

    return {
        "message": "Thumbnail updated successfully.",
        "file_id": file_metadata.FileID,
    }


# __________________________________________________________________________________________________________


@app.get(
    "/courses/certificate/", status_code=200, response_model=List[CertificateDisplay]
)
def get_certificates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role_name != "Employee":
        all_certificate = db.query(Certificate).all()
    else:
        all_certificate = (
            db.query(Certificate).filter(Certificate.user_id == current_user.id).all()
        )
    return all_certificate


@app.get("/courses/{course_id}/", response_model=ListCoursesDisplay)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve the course with all related data like chapters and quizzes if needed
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    is_enrolled = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id, Enrollment.course_id == course_id
        )
        .one_or_none()
    )
    # Assuming CourseFullDisplay includes all necessary data
    # Map the result to CourseFullDisplay, including the is_enrolled flag
    course_display = ListCoursesDisplay.from_orm(course)
    if is_enrolled:
        course_display.is_enrolled = True
        course_display.completed_hours = is_enrolled.completed_hours
        course_display.completion_percentage = is_enrolled.completion_percentage
        course_display.total_questions = len(course.questions)
        course_display.completed_questions = (
            db.query(func.count(QuizCompletions.id))
            .filter(
                QuizCompletions.enrollment_id == is_enrolled.id,
                QuizCompletions.correct_answer == True,
            )
            .scalar()
        )
    return course_display
