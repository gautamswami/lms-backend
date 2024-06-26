from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import models  # Assuming your models and database session are correctly set up
from database import SessionLocal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db
from models import Questions, QuizCompletions, AppStatus
from schemas import (
    QuestionDisplay,
    QuestionCreate,
    QuestionUpdate,
    QuestionGetRequest,
    QuestionSubmission,
    QuizCompletionResponse,
    StatusUpdate,
)
from datetime import datetime
from typing import List, Optional
from fastapi import Query


app = APIRouter(tags=["app_status"])


@app.post("/app_status", response_model=StatusUpdate)
def update_status(status_data: StatusUpdate, db: Session = Depends(get_db)):
    # Create a new status update record
    new_status = AppStatus(
        status_update=status_data.status_update, update_datetime=datetime.now()
    )
    db.add(new_status)
    db.commit()
    db.refresh(new_status)  # Refresh to load the created object with ID and datetime
    return new_status
