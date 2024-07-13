from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.openapi.models import Response
from sqlalchemy.orm import Session

# Import local modules
from auth import get_current_user
from crud import enroll_users, enroll_users_lp
from dependencies import get_db
from models import Course, User, LearningPath, LearningPathEnrollment
from schemas import (CourseUpdate, LearningPathDisplay, LearningPathCreate, AssignLearningPath)

app = APIRouter(tags=['learning_path'])


# ------------------- Course Operations -------------------

# Create a new learning_path

@app.post("/learning_path/", response_model=LearningPathDisplay)
def create_learning_path(learning_path_data: LearningPathCreate, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    new_path = LearningPath(
        name=learning_path_data.name,
        entity=learning_path_data.entity,
        service_line_id=learning_path_data.service_line_id
    )
    db.add(new_path)
    db.commit()
    db.refresh(new_path)
    for course_id in learning_path_data.course_ids:
        new_path.courses.append(db.query(Course).filter(Course.id == course_id).first())
    db.commit()
    return new_path


# Retrieve all learning_path
@app.get("/learning_path/", response_model=List[LearningPathDisplay])
def get_learning_path(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paths = db.query(LearningPath).all()
    return paths


# Retrieve learning_path the current user is enrolled in
@app.get("/learning_path/enrolled/", response_model=List[LearningPathDisplay])
def get_enrolled_learning_paths(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enrolled_paths = db.query(LearningPath).join(LearningPathEnrollment).filter(
        LearningPathEnrollment.user_id == current_user.id).all()
    return enrolled_paths


# Retrieve completed learning_path
@app.get("/learning_path/completed/", response_model=List[LearningPathDisplay])
def get_completed_learning_paths(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    completed_paths = db.query(LearningPath).join(LearningPathEnrollment).filter(
        LearningPathEnrollment.user_id == current_user.id, LearningPathEnrollment.status == "Completed").all()
    return completed_paths


# Retrieve a specific learning_path by ID
@app.get("/learning_path/{learning_path_id}/", response_model=LearningPathDisplay)
def get_learning_path_by_id(learning_path_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return learning_path


@app.put("/learning_path/{learning_path_id}/", response_model=LearningPathDisplay)
def update_learning_path(learning_path_id: int,
                         learning_path_data: CourseUpdate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if path:
        for key, value in learning_path_data.dict().items():
            setattr(path, key, value)
        db.commit()
    return path


@app.delete("/learning_path/{learning_path_id}/", status_code=204)
def update_question(learning_path_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    # DELETE learning_path by id only if there is no Enrollments, delete LearningPathDisplay
    path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    db.delete(path)
    db.commit()
    return Response(status_code=204)


# Assign users to a learning path
@app.post("/learning_path/assign/", status_code=201)
def assign_users_to_learning_path(request: AssignLearningPath,
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)):
    # Retrieve the learning path with its courses
    learning_path = db.query(LearningPath).filter(LearningPath.id == request.learning_path_id).first()
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Iterate over each user ID provided
    for user_id in request.user_ids:
        # Check if the user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue  # Skip if user does not exist, or handle differently as per requirement

        enroll_users_lp(learning_path.id, user_id, request.due_date, db)

        # Assign each course in the learning path to the user
        for course in learning_path.courses:
            enroll_users(course.id, [user_id], db)

    # Commit all changes to the database
    db.commit()

    return {"message": "Users and courses assigned successfully"}
