from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from dependencies import get_db
from models import Feedback, User
from schemas import FeedbackDisplay, FeedbackCreate

app = APIRouter(tags=["feeedback"])


@app.post("/feedbacks/", response_model=FeedbackDisplay)
def create_feedback(feedback_data: FeedbackCreate,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    # Ensure that either user_id or course_id is provided, not both
    if feedback_data.user_id and feedback_data.course_id:
        raise HTTPException(status_code=400, detail="Provide either user_id or course_id, not both.")
    if not feedback_data.user_id and not feedback_data.course_id:
        raise HTTPException(status_code=400, detail="Either user_id or course_id must be provided.")

    new_feedback = Feedback(
        user_id=feedback_data.user_id,
        course_id=feedback_data.course_id,
        description=feedback_data.description,
        rating=feedback_data.rating,
        submitted_by=current_user.id
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    # # Fetch the submitter information
    # submitter = db.query(User).filter(User.id == new_feedback.user_id).first()
    # new_feedback.submitter = submitter

    return new_feedback


@app.get("/feedbacks/", response_model=List[FeedbackDisplay])
def get_feedbacks(user_id: Optional[int] = None, course_id: Optional[int] = None, db: Session = Depends(get_db)):
    if user_id and course_id:
        raise HTTPException(status_code=400, detail="Provide either user_id or course_id for filtering, not both.")

    query = db.query(Feedback)
    if user_id:
        query = query.filter(Feedback.user_id == user_id)
    if course_id:
        query = query.filter(Feedback.course_id == course_id)

    feedbacks = query.all()
    if not feedbacks:
        raise HTTPException(status_code=404, detail="No feedbacks found.")
    return feedbacks


@app.get("/feedbacks/all_courses_of_instructor/", response_model=List[FeedbackDisplay])
def get_feedbacks(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    query = db.query(Feedback).filter(Feedback.course.created_by == current_user.id)
    feedbacks = query.all()
    if not feedbacks:
        raise HTTPException(status_code=404, detail="No feedbacks found.")
    return feedbacks
