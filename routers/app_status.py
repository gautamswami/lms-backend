from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies import get_db
from models import AppStatus
from schemas import (
    StatusUpdate,
)

app = APIRouter(tags=["app_status"])


@app.post("/app_status", response_model=StatusUpdate)
def update_status(status_data: StatusUpdate, db: Session = Depends(get_db)):
    # Fetch the existing status record
    existing_status = db.query(AppStatus).first()

    if existing_status:
        # Update the existing status record
        existing_status.status_update = status_data.status_update
        existing_status.update_datetime = datetime.now()
    else:
        # Create a new status record if none exists
        existing_status = AppStatus(
            status_update=status_data.status_update, update_datetime=datetime.now()
        )
        db.add(existing_status)

    db.commit()
    db.refresh(existing_status)  # Refresh to load the updated object
    return existing_status
