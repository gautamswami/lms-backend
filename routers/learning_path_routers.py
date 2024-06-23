from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.openapi.models import Response
from sqlalchemy.orm import Session

# Import local modules
from auth import get_current_user
from dependencies import get_db
from models import Course, User, Enrollment, LearningPath
from schemas import (CourseUpdate, LearningPathDisplay, LearningPathCreate)

app = APIRouter(tags=['learning_path'])


# ------------------- Course Operations -------------------

# Create a new learning_path

@app.post("/learning_path", response_model=LearningPathDisplay)
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
@app.get("/learning_path", response_model=List[LearningPathDisplay])
def get_learning_path(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paths = db.query(LearningPath).all()
    return paths

# Retrieve learning_path the current user is enrolled in
@app.get("/learning_path/enrolled", response_model=List[LearningPathDisplay])
def get_enrolled_learning_path(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # get enrolled of current_user
    enrolled_courses = db.query(Course).join(Enrollment).filter(Enrollment.user_id == current_user.id).subquery()
    enrolled_paths = db.query(LearningPath).join(enrolled_courses, LearningPath.courses).all()
    return enrolled_paths

# Retrieve completed learning_path
@app.get("/learning_path/completed", response_model=List[LearningPathDisplay])
def get_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Query all learning paths where all courses are completed by the current user
    completed_paths = db.query(LearningPath).filter(
        ~LearningPath.courses.any(
            ~Enrollment.user_id == current_user.id,
            Enrollment.status != "Completed"
        )
    ).all()
    return completed_paths

# Retrieve a specific learning_path by ID
@app.get("/learning_path/{learning_path_id}", response_model=LearningPathDisplay)
def get_learning_path_by_id(learning_path_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return learning_path

@app.put("/learning_path/{learning_path_id}", response_model=LearningPathDisplay)
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

@app.delete("/learning_path/{learning_path_id}", status_code=204)
def update_question(learning_path_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # DELETE learning_path by id only if there is no Enrollments, delete LearningPathDisplay
    path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    db.delete(path)
    db.commit()
    return Response(status_code=204)